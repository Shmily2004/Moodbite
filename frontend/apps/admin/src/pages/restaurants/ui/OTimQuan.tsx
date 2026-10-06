/**
 * Ô tìm quán CÓ TRỄ (debounce) — tách khỏi `RestaurantsPage.tsx` 2026-10-06.
 *
 * VÌ SAO: trước đây mỗi phím gõ ghi thẳng `?q=` lên URL → mỗi phím một lượt gọi
 * `/admin/restaurants` trên bảng ~52.000 dòng. Nay chữ hiện ngay trong ô, nhưng chỉ gửi
 * đi khi người dùng NGỪNG gõ `TRE_MS`.
 *
 * `daGui` nhớ giá trị đã đẩy lên URL: URL đổi từ NGOÀI (nút "Xoá bộ lọc", Back) thì đồng bộ
 * lại ô nhập; còn URL đổi do chính ta gửi thì KHÔNG ghi đè chữ người dùng gõ tiếp trong
 * lúc chờ phản hồi.
 */
import { useEffect, useRef, useState } from 'react';

/** 300 ms: đủ để gõ liền một từ không bắn request, chưa đủ lâu để thấy "đơ". */
export const TRE_MS = 300;

export function OTimQuan({ q, onQuery }: { q: string; onQuery: (q: string) => void }) {
  const [chu, setChu] = useState(q);
  const daGui = useRef(q);
  const onQueryRef = useRef(onQuery);
  onQueryRef.current = onQuery;

  useEffect(() => {
    if (q === daGui.current) return;
    daGui.current = q;
    setChu(q);
  }, [q]);

  useEffect(() => {
    if (chu === daGui.current) return undefined;
    const hen = setTimeout(() => {
      daGui.current = chu;
      onQueryRef.current(chu);
    }, TRE_MS);
    return () => clearTimeout(hen);
  }, [chu]);

  return (
    <input
      className="o-nhap"
      placeholder="Tìm theo tên, địa chỉ hoặc placeId…"
      value={chu}
      onChange={(e) => setChu(e.target.value)}
      aria-label="Tìm quán"
    />
  );
}
