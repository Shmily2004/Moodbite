/**
 * "❤️ Quán & món đã lưu" — MỘT hook cho cả hai trường hợp.
 *
 *   KHÁCH          -> localStorage (xem `luu_cuc_bo.ts`)
 *   ĐÃ ĐĂNG NHẬP   -> bảng `saved_items` ở server qua `/api/v1/me/favorites`
 *
 * VÌ SAO GỘP LÀM MỘT HOOK: giao diện không nên biết dữ liệu đang nằm ở đâu. Nếu tách hai
 * hook thì mỗi thẻ món phải tự hỏi "tôi đang đăng nhập chưa" — đúng thứ logic sẽ bị chép
 * đi chép lại rồi lệch nhau.
 *
 * ĐỒNG BỘ MỘT LẦN KHI ĐĂNG NHẬP: những thứ khách đã lưu trên máy được ĐẨY LÊN server rồi
 * xoá bản cục bộ. Không làm thế thì người dùng lưu 5 món, đăng ký tài khoản, và thấy danh
 * sách trống — mất dữ liệu ngay tại bước ta đang mời họ đăng ký.
 *
 * CẬP NHẬT LẠC QUAN: bấm tim là đổi giao diện NGAY, gọi API sau. Lỗi thì trả về trạng
 * thái cũ và báo. Đợi mạng xong mới đổi màu trái tim làm cả app có cảm giác chậm.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { authApi } from '@/shared/api';
import { useUserSessionContext } from '@/entities/user';
import {
  doc_cuc_bo,
  ghi_cuc_bo,
  khoa,
  xoa_cuc_bo,
} from './luu_cuc_bo';
import type { LoaiMuc, MucYeuThich } from './luu_cuc_bo';

export type { LoaiMuc, MucYeuThich };

export interface UseFavoritesResult {
  /** Mọi mục đã lưu, mới nhất đứng đầu. */
  items: MucYeuThich[];
  restaurants: MucYeuThich[];
  dishes: MucYeuThich[];
  isSaved: (itemType: LoaiMuc, itemId: string) => boolean;
  /** Lưu nếu chưa có, bỏ lưu nếu đã có. */
  toggle: (muc: MucYeuThich) => void;
  /** `true` khi dữ liệu nằm ở server (đã đăng nhập). Giao diện dùng để nói đúng sự thật. */
  dongBo: boolean;
  loading: boolean;
  error: string | null;
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
            });
          }
          if (cuc_bo.length > 0) xoa_cuc_bo();
        }

        const data = await authApi.favorites();
        if (!con_song) return;
        setItems(
          data.items.map((x) => ({
            itemType: x.item_type as LoaiMuc,
            itemId: x.item_id,
            name: x.name,
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
    (itemType: LoaiMuc, itemId: string) =>
      items.some((x) => x.itemType === itemType && x.itemId === itemId),
    [items],
  );

  const toggle = useCallback(
    (muc: MucYeuThich) => {
      const dang_co = items.some((x) => khoa(x) === khoa(muc));
      const truoc = items;
      const sau = dang_co ? items.filter((x) => khoa(x) !== khoa(muc)) : [muc, ...items];

      setItems(sau); // cập nhật lạc quan

      if (!daDangNhap) {
        ghi_cuc_bo(sau);
        return;
      }

      const goi = dang_co
        ? authApi.removeFavorite(muc.itemType, muc.itemId)
        : authApi.saveFavorite({
            item_type: muc.itemType,
            item_id: muc.itemId,
            name: muc.name,
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

  return {
    items,
    restaurants: items.filter((x) => x.itemType === 'restaurant'),
    dishes: items.filter((x) => x.itemType === 'dish'),
    isSaved,
    toggle,
    dongBo: daDangNhap,
    loading,
    error,
  };
}
