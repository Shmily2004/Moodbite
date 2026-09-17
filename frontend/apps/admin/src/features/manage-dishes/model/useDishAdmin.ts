/**
 * VIEWMODEL của màn "Quản lý món ăn".
 *
 * Chỉ điều phối: giữ từ khoá + bộ lọc + trang, gọi API, giữ trạng thái tải/lỗi. Không lọc,
 * không đếm và không xếp lại ở đây — backend đã làm (`list_dishes_admin.py`). Lọc hay đếm
 * thêm ở frontend sẽ lệch với `total`/`counts` mà chính backend trả về.
 *
 * PHÂN TRANG Ở SERVER (2026-09-16). Trước đó bảng bị cắt cứng 50 dòng: 805 món còn lại
 * không có cách nào xem ngoài việc gõ tìm.
 *
 * ⚠️ TÌM KIẾM CÓ HOÃN (debounce). Gõ "bún chả" là 7 lần đổi state; không hoãn thì thành
 * 7 request, và request về sau có thể tới TRƯỚC request trước đó khiến bảng nhảy về kết
 * quả cũ. `LUOT_HOAN_MS` đủ ngắn để không thấy giật, đủ dài để gộp một lần gõ.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { adminApi, ApiError } from '@/shared/api';
import type { AdminDishRow, LocMon } from '@/shared/api';

const LUOT_HOAN_MS = 300;
export const CO_TRANG_MON_MAC_DINH = 20;
const CAC_CO_TRANG = [10, 20, 50, 100];

export interface UseDishAdminResult {
  rows: AdminDishRow[];
  /** Tổng khớp (từ khoá + bộ lọc) — để phân trang. */
  total: number;
  /** Số món của từng bộ lọc — số trên nút lọc. Rỗng khi chưa tải. */
  counts: Partial<Record<LocMon, number>>;
  /** Hai thẻ số đầu trang, trên TOÀN BỘ danh mục. `null` = chưa tải. */
  dishesTotal: number | null;
  dishesWithRestaurants: number | null;
  query: string;
  setQuery: (q: string) => void;
  filter: LocMon;
  setFilter: (f: LocMon) => void;
  page: number;
  setPage: (p: number) => void;
  pageSize: number;
  setPageSize: (n: number) => void;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

/** Khoá hợp lệ trên URL. Khoá lạ -> `all`, không báo lỗi: một đường dẫn đã lưu từ bản
 *  cũ không đáng làm hỏng cả trang. */
const HOP_LE: LocMon[] = [
  'all',
  'with_restaurants',
  'without_restaurants',
  'missing_image',
  'missing_description',
];

function soDuong(chu: string | null, macDinh: number): number {
  const n = Number(chu);
  return Number.isInteger(n) && n > 0 ? n : macDinh;
}

export function useDishAdmin(): UseDishAdminResult {
  // BỘ LỌC + TRANG NẰM TRÊN URL, không phải state trong bộ nhớ. Nhờ vậy hộp "Cần xử lý" ở
  // trang Tổng quan bấm sang được đúng danh sách đã lọc, người quản trị gửi link cho nhau
  // được, và bấm Back từ trang chi tiết món quay về ĐÚNG trang đang xem.
  const [thamSo, setThamSo] = useSearchParams();
  const query = thamSo.get('q') ?? '';
  const tuUrl = thamSo.get('filter') as LocMon | null;
  const filter: LocMon = tuUrl && HOP_LE.includes(tuUrl) ? tuUrl : 'all';
  const page = soDuong(thamSo.get('trang'), 1);
  const coTuUrl = soDuong(thamSo.get('so_dong'), CO_TRANG_MON_MAC_DINH);
  const pageSize = CAC_CO_TRANG.includes(coTuUrl) ? coTuUrl : CO_TRANG_MON_MAC_DINH;

  const ghiUrl = useCallback(
    (thay: { q?: string; f?: LocMon; trang?: number; co?: number }) => {
      const q = thay.q ?? query;
      const f = thay.f ?? filter;
      const co = thay.co ?? pageSize;
      const trang = thay.trang ?? page;
      const moi = new URLSearchParams();
      if (q) moi.set('q', q);
      if (f !== 'all') moi.set('filter', f);
      if (trang > 1) moi.set('trang', String(trang));
      if (co !== CO_TRANG_MON_MAC_DINH) moi.set('so_dong', String(co));
      // `replace` để mỗi ký tự gõ vào ô tìm KHÔNG tạo một mục mới trong lịch sử.
      setThamSo(moi, { replace: true });
    },
    [setThamSo, query, filter, page, pageSize],
  );

  // Đổi từ khoá / bộ lọc / cỡ trang thì VỀ TRANG 1: ở lại trang 7 của một kết quả chỉ có
  // 2 trang là màn hình trống không giải thích được.
  const setQuery = useCallback((q: string) => ghiUrl({ q, trang: 1 }), [ghiUrl]);
  const setFilter = useCallback((f: LocMon) => ghiUrl({ f, trang: 1 }), [ghiUrl]);
  const setPage = useCallback((trang: number) => ghiUrl({ trang }), [ghiUrl]);
  const setPageSize = useCallback((co: number) => ghiUrl({ co, trang: 1 }), [ghiUrl]);

  const [rows, setRows] = useState<AdminDishRow[]>([]);
  const [total, setTotal] = useState(0);
  const [counts, setCounts] = useState<Partial<Record<LocMon, number>>>({});
  const [dishesTotal, setDishesTotal] = useState<number | null>(null);
  const [dishesWithRestaurants, setDishesWithRestaurants] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lan, setLan] = useState(0);

  // Đánh số mỗi lần gọi. Chỉ nhận kết quả của lần gọi MỚI NHẤT.
  const soLuot = useRef(0);

  useEffect(() => {
    const luot = ++soLuot.current;
    let conSong = true;
    setLoading(true);

    const hen = setTimeout(() => {
      adminApi
        .listDishes({ q: query || null, filter, page, pageSize })
        .then((kq) => {
          if (!conSong || luot !== soLuot.current) return;
          setRows(kq.results);
          setTotal(kq.total);
          setCounts((kq.counts ?? {}) as Partial<Record<LocMon, number>>);
          setDishesTotal(kq.dishes_total ?? null);
          setDishesWithRestaurants(kq.dishes_with_restaurants ?? null);
          setError(null);
        })
        .catch((err: unknown) => {
          if (!conSong || luot !== soLuot.current) return;
          setError(err instanceof ApiError ? err.message : (err as Error).message);
        })
        .finally(() => {
          if (conSong && luot === soLuot.current) setLoading(false);
        });
    }, LUOT_HOAN_MS);

    return () => {
      conSong = false;
      clearTimeout(hen);
    };
  }, [query, filter, page, pageSize, lan]);

  const reload = useCallback(() => setLan((n) => n + 1), []);

  return {
    rows,
    total,
    counts,
    dishesTotal,
    dishesWithRestaurants,
    query,
    setQuery,
    filter,
    setFilter,
    page,
    setPage,
    pageSize,
    setPageSize,
    loading,
    error,
    reload,
  };
}
