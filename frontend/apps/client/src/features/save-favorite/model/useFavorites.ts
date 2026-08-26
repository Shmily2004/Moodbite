/**
 * "Món yêu thích" + "Đã lưu" — MỘT hook cho cả hai danh sách, cả hai trường hợp.
 *
 *   KHÁCH          -> localStorage (xem `luu_cuc_bo.ts`)
 *   ĐÃ ĐĂNG NHẬP   -> bảng `saved_items` ở server qua `/api/v1/me/favorites`
 *
 * HAI DANH SÁCH TÁCH BẠCH (chủ dự án chốt 2026-08-26):
 *
 *   `favorite`  trái tim   "Món yêu thích"  — món tôi THÍCH
 *   `bookmark`  dấu trang  "Đã lưu"         — món tôi ĐỊNH ĂN, để dành xem sau
 *
 * Một món nằm được ở CẢ HAI cùng lúc, và bỏ tim KHÔNG đụng tới dấu trang. Vì vậy mọi
 * hàm ở đây đều nhận `listType`, và khoá định danh phải gộp nó vào — xem `khoa()`.
 *
 * VÌ SAO MỘT HOOK CHO CẢ HAI DANH SÁCH thay vì gọi hai lần: một thẻ món cần biết CÙNG
 * LÚC tim có bật không và dấu trang có bật không. Tách hai hook là hai lượt mạng cho
 * cùng một bảng, và hai bộ state phải tự đồng bộ với nhau.
 *
 * VÌ SAO GỘP KHÁCH VÀ NGƯỜI ĐÃ ĐĂNG NHẬP: giao diện không nên biết dữ liệu nằm ở đâu.
 * Tách hai hook thì mỗi thẻ món phải tự hỏi "tôi đang đăng nhập chưa" — đúng thứ logic
 * sẽ bị chép đi chép lại rồi lệch nhau.
 *
 * ĐỒNG BỘ MỘT LẦN KHI ĐĂNG NHẬP: những thứ khách đã lưu trên máy được ĐẨY LÊN server rồi
 * xoá bản cục bộ. Không làm thế thì người dùng lưu 5 món, đăng ký tài khoản, và thấy danh
 * sách trống — mất dữ liệu ngay tại bước ta đang mời họ đăng ký.
 *
 * CẬP NHẬT LẠC QUAN: bấm là đổi giao diện NGAY, gọi API sau. Lỗi thì trả về trạng thái cũ
 * và báo. Đợi mạng xong mới đổi màu trái tim làm cả app có cảm giác chậm.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { authApi } from '@/shared/api';
import { useUserSessionContext } from '@/entities/user';
import {
  DANH_SACH_MAC_DINH,
  doc_cuc_bo,
  ghi_cuc_bo,
  khoa,
  xoa_cuc_bo,
} from './luu_cuc_bo';
import type { LoaiDanhSach, LoaiMuc, MucYeuThich } from './luu_cuc_bo';

export type { LoaiDanhSach, LoaiMuc, MucYeuThich };
export { DANH_SACH_MAC_DINH };

/** Một danh sách đã tách sẵn theo loại, để giao diện khỏi phải tự lọc. */
export interface NhomDaLuu {
  items: MucYeuThich[];
  restaurants: MucYeuThich[];
  dishes: MucYeuThich[];
}

export interface UseFavoritesResult {
  /** Mọi mục của CẢ HAI danh sách, mới nhất đứng đầu. */
  items: MucYeuThich[];
  /** Trái tim — "Món yêu thích". */
  favorite: NhomDaLuu;
  /** Dấu trang — "Đã lưu". */
  bookmark: NhomDaLuu;
  isSaved: (itemType: LoaiMuc, itemId: string, listType?: LoaiDanhSach) => boolean;
  /** Thêm vào danh sách nếu chưa có, bỏ ra nếu đã có. Chỉ động vào ĐÚNG danh sách được nêu. */
  toggle: (muc: MucYeuThich) => void;
  /** `true` khi dữ liệu nằm ở server (đã đăng nhập). Giao diện dùng để nói đúng sự thật. */
  dongBo: boolean;
  loading: boolean;
  error: string | null;
}

function nhom(items: MucYeuThich[], danh_sach: LoaiDanhSach): NhomDaLuu {
  const cua_nhom = items.filter(
    (x) => (x.listType ?? DANH_SACH_MAC_DINH) === danh_sach,
  );
  return {
    items: cua_nhom,
    restaurants: cua_nhom.filter((x) => x.itemType === 'restaurant'),
    dishes: cua_nhom.filter((x) => x.itemType === 'dish'),
  };
}

export function useFavorites(): UseFavoritesResult {
  const session = useUserSessionContext();
  const daDangNhap = session.isLoggedIn;

  const [items, setItems] = useState<MucYeuThich[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Chỉ đẩy dữ liệu cục bộ lên server ĐÚNG MỘT LẦN cho mỗi lần đăng nhập. Không có cờ
  // này thì mỗi lần hook chạy lại sẽ đẩy lại, và mục người dùng vừa cố ý bỏ lưu sẽ
  // "sống lại".
  const daDongBo = useRef(false);

  useEffect(() => {
    if (!daDangNhap) {
      daDongBo.current = false;
      setItems(doc_cuc_bo());
      setError(null);
      return;
    }

    let con_song = true;
    setLoading(true);

    const nap = async () => {
      try {
        // Đẩy phần khách đã lưu trên máy lên trước, rồi mới tải danh sách đầy đủ về —
        // thứ tự này bảo đảm kết quả cuối cùng có cả hai nguồn.
        if (!daDongBo.current) {
          daDongBo.current = true;
          const cuc_bo = doc_cuc_bo();
          for (const muc of cuc_bo) {
            await authApi.saveFavorite({
              item_type: muc.itemType,
              item_id: muc.itemId,
              name: muc.name,
              // Giữ nguyên danh sách khách đã chọn lúc chưa đăng nhập.
              list_type: muc.listType ?? DANH_SACH_MAC_DINH,
            });
          }
          if (cuc_bo.length > 0) xoa_cuc_bo();
        }

        // Bỏ trống cả hai tham số = lấy CẢ HAI danh sách trong một lượt.
        const data = await authApi.favorites();
        if (!con_song) return;
        setItems(
          data.items.map((x) => ({
            itemType: x.item_type as LoaiMuc,
            itemId: x.item_id,
            name: x.name,
            listType: (x.list_type as LoaiDanhSach) ?? DANH_SACH_MAC_DINH,
          })),
        );
        setError(null);
      } catch (err) {
        if (!con_song) return;
        // Lỗi mạng KHÔNG được làm trắng danh sách: hiện bản cục bộ còn hơn không có gì.
        setItems(doc_cuc_bo());
        setError(err instanceof Error ? err.message : 'Không tải được danh sách đã lưu.');
      } finally {
        if (con_song) setLoading(false);
      }
    };

    void nap();
    return () => {
      con_song = false;
    };
  }, [daDangNhap]);

  const isSaved = useCallback(
    (itemType: LoaiMuc, itemId: string, listType: LoaiDanhSach = DANH_SACH_MAC_DINH) =>
      items.some((x) => khoa(x) === khoa({ itemType, itemId, listType })),
    [items],
  );

  const toggle = useCallback(
    (muc: MucYeuThich) => {
      const day_du: MucYeuThich = {
        ...muc,
        listType: muc.listType ?? DANH_SACH_MAC_DINH,
      };
      const dang_co = items.some((x) => khoa(x) === khoa(day_du));
      const truoc = items;
      const sau = dang_co
        ? items.filter((x) => khoa(x) !== khoa(day_du))
        : [day_du, ...items];

      setItems(sau); // cập nhật lạc quan

      if (!daDangNhap) {
        ghi_cuc_bo(sau);
        return;
      }

      const goi = dang_co
        ? authApi.removeFavorite(day_du.itemType, day_du.itemId, day_du.listType)
        : authApi.saveFavorite({
            item_type: day_du.itemType,
            item_id: day_du.itemId,
            name: day_du.name,
            list_type: day_du.listType,
          });

      void goi.catch((err: unknown) => {
        // Trả về ĐÚNG trạng thái trước đó. Giữ nguyên giao diện sẽ nói dối người dùng
        // rằng đã lưu, rồi tải lại trang là mất.
        setItems(truoc);
        setError(err instanceof Error ? err.message : 'Không lưu được. Thử lại nhé.');
      });
    },
    [items, daDangNhap],
  );

  const favorite = useMemo(() => nhom(items, 'favorite'), [items]);
  const bookmark = useMemo(() => nhom(items, 'bookmark'), [items]);

  return {
    items,
    favorite,
    bookmark,
    isSaved,
    toggle,
    dongBo: daDangNhap,
    loading,
    error,
  };
}
