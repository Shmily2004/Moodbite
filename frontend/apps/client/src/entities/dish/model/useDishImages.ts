/**
 * Tra ẢNH MÓN cho một nhóm `dish_id` — dùng ở trang tài khoản, nơi danh sách đã lưu / đã
 * xem chỉ có `id` + `name` (bảng `saved_items` và localStorage không chụp lại ảnh).
 *
 * VÌ SAO GỌI `GET /dishes/{id}` TỪNG MÓN: không có endpoint nào trả ảnh theo lô. Thêm một
 * endpoint như vậy là đổi hợp đồng API (CLAUDE.md mục 5) — phải bàn trước. Để giới hạn chi
 * phí: chỉ tra tối đa `SO_MON_TOI_DA` món, mỗi món đúng một lần trong đời component, và
 * lỗi thì coi như "không có ảnh" (thẻ tự lui về ô màu sinh từ tên).
 *
 * ⚠️ Thiếu ảnh là chuyện BÌNH THƯỜNG (140/747 món chưa có ảnh), không phải lỗi — nên hook
 * này KHÔNG báo lỗi lên giao diện.
 */
import { useEffect, useRef, useState } from 'react';
import { api } from '@/shared/api';

/** Đủ cho hai hàng thẻ ngang ở tab Tổng quan (đã lưu + đã xem), không tra cả trăm món. */
const SO_MON_TOI_DA = 16;

/** `dish_id` -> URL ảnh. `null` = đã tra, món không có ảnh. Chưa có khoá = chưa tra xong. */
export type AnhMon = Record<string, string | null>;

export function useDishImages(dishIds: string[]): AnhMon {
  const [anh, setAnh] = useState<AnhMon>({});
  // Nhớ id ĐÃ GỬI đi tra, để đổi danh sách (bỏ lưu một món) không tra lại cả loạt.
  const daTra = useRef(new Set<string>());

  // Khoá chuỗi thay vì mảng: mảng mới mỗi lần render sẽ làm effect chạy lại vô hạn.
  const khoa = Array.from(new Set(dishIds)).slice(0, SO_MON_TOI_DA).join('|');

  useEffect(() => {
    const canTra = (khoa ? khoa.split('|') : []).filter((id) => !daTra.current.has(id));
    if (canTra.length === 0) return;

    let conSong = true;
    canTra.forEach((id) => daTra.current.add(id));

    void Promise.all(
      canTra.map((id) =>
        api
          .dishDetail(id)
          .then((mon) => [id, mon?.image_url ?? null] as const)
          .catch(() => [id, null] as const),
      ),
    ).then((cap) => {
      if (!conSong) return;
      setAnh((cu) => ({ ...cu, ...Object.fromEntries(cap) }));
    });

    return () => {
      conSong = false;
      // Bị huỷ giữa chừng thì cho phép tra lại ở lần sau, nếu không món đó mất ảnh mãi.
      canTra.forEach((id) => daTra.current.delete(id));
    };
  }, [khoa]);

  return anh;
}
