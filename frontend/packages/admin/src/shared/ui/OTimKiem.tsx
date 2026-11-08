/**
 * Ô tìm kiếm CÓ TRỄ (debounce), dùng chung cho danh sách quán và danh sách món.
 *
 * VÌ SAO CÓ TRỄ: trước đây mỗi phím gõ ghi thẳng `?q=` lên URL → mỗi phím một lượt gọi API
 * trên bảng lớn (~52.000 quán). Nay chữ hiện ngay trong ô, nhưng chỉ đẩy lên URL khi người
 * dùng NGỪNG gõ `TRE_MS`.
 *
 * `daGui` nhớ giá trị đã đẩy lên URL: URL đổi từ NGOÀI (nút "Xoá bộ lọc", Back) thì đồng bộ
 * lại ô nhập; còn URL đổi do chính ta gửi thì KHÔNG ghi đè chữ người dùng gõ tiếp trong
 * lúc chờ phản hồi.
 *
 * ⚠️ IME TIẾNG VIỆT (lỗi 2026-11-08, admin "không gõ được vietkey"): bộ gõ Telex/VNI giữ
 * chữ đang soạn dở (vd "tr" + "ế" chưa chốt) ở trạng thái composition. Nếu trong lúc đó ta
 * đẩy giá trị lên URL / đặt lại ô, bộ gõ mất chuỗi đang soạn và dấu bị rơi. Nên:
 *   - khi đang composition thì KHÔNG lên lịch gửi;
 *   - hết composition (`compositionend`) mới lên lịch, với chữ đã chốt.
 * `dangGhep` là STATE (không phải ref) để effect chạy lại đúng lúc composition kết thúc.
 */
import { useEffect, useRef, useState } from 'react';

/** 300 ms: đủ để gõ liền một từ không bắn request, chưa đủ lâu để thấy "đơ". */
export const TRE_MS = 300;

export interface OTimKiemProps {
  q: string;
  onQuery: (q: string) => void;
  placeholder: string;
  label: string;
}

export function OTimKiem({ q, onQuery, placeholder, label }: OTimKiemProps) {
  const [chu, setChu] = useState(q);
  const [dangGhep, setDangGhep] = useState(false);
  const daGui = useRef(q);
  const onQueryRef = useRef(onQuery);
  onQueryRef.current = onQuery;

  useEffect(() => {
    if (q === daGui.current) return;
    daGui.current = q;
    setChu(q);
  }, [q]);

  useEffect(() => {
    if (dangGhep) return undefined; // đang soạn dấu: chưa gửi, xem ghi chú đầu file
    if (chu === daGui.current) return undefined;
    const hen = setTimeout(() => {
      daGui.current = chu;
      onQueryRef.current(chu);
    }, TRE_MS);
    return () => clearTimeout(hen);
  }, [chu, dangGhep]);

  return (
    <input
      className="o-nhap"
      type="search"
      placeholder={placeholder}
      value={chu}
      onChange={(e) => setChu(e.target.value)}
      onCompositionStart={() => setDangGhep(true)}
      onCompositionEnd={() => setDangGhep(false)}
      aria-label={label}
    />
  );
}
