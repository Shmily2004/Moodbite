/**
 * VIEWMODEL của việc quản lý quán: tải trang danh sách + thẻ số, lọc, chọn nhiều, ẩn/bỏ
 * ẩn (từng quán hoặc hàng loạt), sửa trường mô tả, thêm quán.
 *
 * KHÔNG chứa quy tắc nghiệp vụ. "Trường nào sửa được", "quán nhập tay là gì", đếm tổng —
 * đều do BACKEND quyết; ở đây chỉ gửi đi và hiển thị kết quả trả về.
 *
 * PHÂN TRANG Ở SERVER (2026-09-16). Mọi bộ lọc + trang nằm trên URL: hộp "Cần xử lý" ở
 * trang Tổng quan bấm sang được đúng danh sách, và gửi link cho nhau được.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import type {
  AdminCreateRestaurantRequest,
  AdminRestaurantStatsData,
  AdminRestaurantSummary,
  AdminUpdateRestaurantRequest,
} from '@moodbite/api-client';
import { ApiError, adminApi } from '@/shared/api';

export const CO_TRANG_QUAN_MAC_DINH = 20;
const CAC_CO_TRANG = [10, 20, 50, 100];

export type TrangThaiQuan = 'visible' | 'hidden';

export interface BoLocQuan {
  q: string;
  district: string | null;
  source: string | null;
  status: TrangThaiQuan | null;
  /** Bộ lọc "việc cần xử lý" (`dong_tam` | `thieu_lien_he`) bấm sang từ trang Tổng quan. */
  loc: string | null;
}

export interface UseRestaurantAdminOptions {
  /** Gọi khi backend trả 401 — token hết hạn giữa phiên làm việc. */
  onExpired: () => void;
}

export interface UseRestaurantAdminResult {
  restaurants: AdminRestaurantSummary[];
  /** Tổng số quán KHỚP BỘ LỌC (không phải số dòng của trang). */
  total: number;
  stats: AdminRestaurantStatsData | null;
  filters: BoLocQuan;
  setFilters: (thay: Partial<BoLocQuan>) => void;
  clearFilters: () => void;
  /** Bỏ bộ lọc "việc cần xử lý" mà không đụng tới bộ lọc khác. */
  clearLoc: () => void;
  /** Tên cũ, giữ cho chỗ đang dùng. */
  loc: string | null;
  query: string;
  setQuery: (value: string) => void;
  page: number;
  setPage: (p: number) => void;
  pageSize: number;
  setPageSize: (n: number) => void;
  loading: boolean;
  error: string | null;
  notice: string | null;
  reload: () => Promise<void>;
  /** Các `restaurant_id` đang được chọn TRÊN TRANG HIỆN TẠI. */
  selected: Set<string>;
  toggleSelected: (id: string) => void;
  toggleSelectAllOnPage: () => void;
  bulkSetVisibility: (isActive: boolean) => Promise<void>;
  bulkBusy: boolean;
  toggleHidden: (restaurant: AdminRestaurantSummary) => Promise<void>;
  saveChanges: (
    restaurantId: string,
    changes: AdminUpdateRestaurantRequest,
  ) => Promise<boolean>;
  /** Thêm quán mới. Trả `true` khi thành công (form tự dọn), `false` khi lỗi. */
  createRestaurant: (body: AdminCreateRestaurantRequest) => Promise<boolean>;
}

/** Một lần đổi URL: `null` = XOÁ bộ lọc đó, vắng mặt = giữ nguyên. */
type ThayDoiLoc = { [K in keyof BoLocQuan]?: BoLocQuan[K] | null } & {
  trang?: number;
  co?: number;
};

function soDuong(chu: string | null, macDinh: number): number {
  const n = Number(chu);
  return Number.isInteger(n) && n > 0 ? n : macDinh;
}

export function useRestaurantAdmin({
  onExpired,
}: UseRestaurantAdminOptions): UseRestaurantAdminResult {
  const [thamSo, setThamSo] = useSearchParams();
  const trangThaiUrl = thamSo.get('trang_thai');
  const filters: BoLocQuan = {
    q: thamSo.get('q') ?? '',
    district: thamSo.get('khu_vuc'),
    source: thamSo.get('nguon'),
    status:
      trangThaiUrl === 'visible' || trangThaiUrl === 'hidden' ? trangThaiUrl : null,
    loc: thamSo.get('loc'),
  };
  const page = soDuong(thamSo.get('trang'), 1);
  const coUrl = soDuong(thamSo.get('so_dong'), CO_TRANG_QUAN_MAC_DINH);
  const pageSize = CAC_CO_TRANG.includes(coUrl) ? coUrl : CO_TRANG_QUAN_MAC_DINH;

  const ghiUrl = useCallback(
    (thay: ThayDoiLoc) => {
      const hienTai = new URLSearchParams(thamSo);
      const dat = (khoa: string, giaTri: string | null | undefined) => {
        if (giaTri) hienTai.set(khoa, giaTri);
        else hienTai.delete(khoa);
      };
      if ('q' in thay) dat('q', thay.q);
      if ('district' in thay) dat('khu_vuc', thay.district);
      if ('source' in thay) dat('nguon', thay.source);
      if ('status' in thay) dat('trang_thai', thay.status);
      if ('loc' in thay) dat('loc', thay.loc);
      if (thay.co != null) {
        dat('so_dong', thay.co === CO_TRANG_QUAN_MAC_DINH ? null : String(thay.co));
      }
      // Đổi BẤT KỲ bộ lọc nào thì về trang 1 — trừ khi chính lệnh này là đổi trang.
      const trang = thay.trang ?? 1;
      dat('trang', trang > 1 ? String(trang) : null);
      setThamSo(hienTai, { replace: true });
    },
    [thamSo, setThamSo],
  );

  const setFilters = useCallback((thay: Partial<BoLocQuan>) => ghiUrl(thay), [ghiUrl]);
  const clearFilters = useCallback(
    () => ghiUrl({ q: null, district: null, source: null, status: null, loc: null }),
    [ghiUrl],
  );
  const clearLoc = useCallback(() => ghiUrl({ loc: null, trang: page }), [ghiUrl, page]);
  const setQuery = useCallback((q: string) => ghiUrl({ q }), [ghiUrl]);
  const setPage = useCallback((trang: number) => ghiUrl({ trang }), [ghiUrl]);
  const setPageSize = useCallback((co: number) => ghiUrl({ co }), [ghiUrl]);

  const [restaurants, setRestaurants] = useState<AdminRestaurantSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [stats, setStats] = useState<AdminRestaurantStatsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [bulkBusy, setBulkBusy] = useState(false);

  const abortRef = useRef<AbortController | null>(null);

  /** Token hết hạn -> đưa người dùng về màn đăng nhập thay vì hiện lỗi khó hiểu. */
  const handleError = useCallback(
    (err: unknown) => {
      if (err instanceof ApiError && err.code === 'UNAUTHORIZED') {
        onExpired();
        return;
      }
      setError(err instanceof ApiError ? err.userMessage : (err as Error).message);
    },
    [onExpired],
  );

  const { q, district, source, status, loc } = filters;

  const reload = useCallback(async () => {
    // Huỷ request cũ: gõ nhanh vào ô tìm kiếm sẽ tạo nhiều request, và request cũ về
    // sau có thể ghi đè kết quả mới. Đây đúng là bug bản frontend v1 từng mắc.
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    try {
      const data = await adminApi.listRestaurants(
        {
          q: q || null,
          page,
          pageSize,
          district,
          source,
          status,
          loc,
          includeHidden: true,
        },
        { signal: controller.signal },
      );
      setRestaurants(data.results);
      // `total_matched` có từ khi backend phân trang; thiếu (backend cũ) thì lui về số dòng.
      setTotal(data.total_matched ?? data.total);
      // Đổi trang = danh sách khác -> bỏ chọn. Giữ lựa chọn vô hình ở trang khác là cách
      // chắc chắn nhất để ẩn nhầm quán người quản trị không còn nhìn thấy.
      setSelected(new Set());
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return;
      handleError(err);
    } finally {
      if (abortRef.current === controller) setLoading(false);
    }
  }, [q, page, pageSize, district, source, status, loc, handleError]);

  const taiThongKe = useCallback(async () => {
    try {
      setStats(await adminApi.restaurantStats());
    } catch (err) {
      // Thẻ số hỏng KHÔNG chặn bảng: bảng vẫn dùng được, chỉ thiếu thẻ và ô chọn.
      if (err instanceof ApiError && err.code === 'UNAUTHORIZED') onExpired();
    }
  }, [onExpired]);

  useEffect(() => {
    void reload();
  }, [reload]);

  useEffect(() => {
    void taiThongKe();
  }, [taiThongKe]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const thayDong = useCallback((moi: AdminRestaurantSummary[]) => {
    const theoMa = new Map(moi.map((r) => [r.restaurant_id, r]));
    // Cập nhật tại chỗ thay vì tải lại cả danh sách: giữ nguyên vị trí cuộn.
    setRestaurants((cu) => cu.map((r) => theoMa.get(r.restaurant_id) ?? r));
  }, []);

  const toggleHidden = useCallback(
    async (restaurant: AdminRestaurantSummary) => {
      if (!restaurant.restaurant_id) return;
      setError(null);
      try {
        const updated = restaurant.is_active
          ? await adminApi.hideRestaurant(restaurant.restaurant_id)
          : await adminApi.restoreRestaurant(restaurant.restaurant_id);
        thayDong([updated]);
        setNotice(
          updated.is_active
            ? `Đã bỏ ẩn "${updated.name}".`
            : `Đã ẩn "${updated.name}" khỏi kết quả tìm kiếm của người dùng.`,
        );
        void taiThongKe();
      } catch (err) {
        handleError(err);
      }
    },
    [handleError, thayDong, taiThongKe],
  );

  const toggleSelected = useCallback((id: string) => {
    setSelected((cu) => {
      const moi = new Set(cu);
      if (moi.has(id)) moi.delete(id);
      else moi.add(id);
      return moi;
    });
  }, []);

  const toggleSelectAllOnPage = useCallback(() => {
    const ma = restaurants.map((r) => r.restaurant_id).filter((x): x is string => !!x);
    setSelected((cu) => (ma.every((m) => cu.has(m)) ? new Set() : new Set(ma)));
  }, [restaurants]);

  const bulkSetVisibility = useCallback(
    async (isActive: boolean) => {
      const ma = [...selected];
      if (ma.length === 0) return;
      setBulkBusy(true);
      setError(null);
      try {
        const kq = await adminApi.bulkSetVisibility(ma, isActive);
        thayDong(kq.updated);
        setSelected(new Set());
        const viec = isActive ? 'bỏ ẩn' : 'ẩn';
        const khongCo = kq.not_found ?? [];
        setNotice(
          `Đã ${viec} ${kq.updated.length} quán.` +
            (khongCo.length
              ? ` ${khongCo.length} mã không còn tồn tại: ${khongCo.join(', ')}.`
              : ''),
        );
        void taiThongKe();
      } catch (err) {
        handleError(err);
      } finally {
        setBulkBusy(false);
      }
    },
    [selected, handleError, thayDong, taiThongKe],
  );

  const saveChanges = useCallback(
    async (restaurantId: string, changes: AdminUpdateRestaurantRequest) => {
      setError(null);
      try {
        const updated = await adminApi.updateRestaurant(restaurantId, changes);
        thayDong([updated]);
        setNotice(`Đã lưu thay đổi cho "${updated.name}".`);
        return true;
      } catch (err) {
        handleError(err);
        return false;
      }
    },
    [handleError, thayDong],
  );

  const createRestaurant = useCallback(
    async (body: AdminCreateRestaurantRequest) => {
      setError(null);
      try {
        const created = await adminApi.createRestaurant(body);
        // Chèn lên ĐẦU danh sách để người nhập thấy ngay kết quả việc mình vừa làm.
        setRestaurants((current) => [created, ...current]);
        setTotal((n) => n + 1);
        setNotice(
          `Đã thêm "${created.name}". Mã: ${created.restaurant_id} ` +
            '(tiền tố "manual:" cho biết quán này do người nhập tay).',
        );
        void taiThongKe();
        return true;
      } catch (err) {
        handleError(err);
        return false;
      }
    },
    [handleError, taiThongKe],
  );

  return {
    restaurants,
    total,
    stats,
    filters,
    setFilters,
    clearFilters,
    clearLoc,
    loc,
    query: q,
    setQuery,
    page,
    setPage,
    pageSize,
    setPageSize,
    loading,
    error,
    notice,
    reload,
    selected,
    toggleSelected,
    toggleSelectAllOnPage,
    bulkSetVisibility,
    bulkBusy,
    toggleHidden,
    saveChanges,
    createRestaurant,
  };
}
