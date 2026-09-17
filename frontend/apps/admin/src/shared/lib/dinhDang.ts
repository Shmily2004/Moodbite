/**
 * Định dạng HIỂN THỊ dùng chung. Chỉ là quy tắc trình bày — không có nghiệp vụ.
 */

export function soVN(n: number): string {
  return n.toLocaleString('vi-VN');
}

/** "34,9%". Tổng 0 -> "—" (không chia cho 0 rồi hiện "NaN%" hay giả vờ "0%"). */
export function phanTramVN(phan: number, tong: number): string {
  if (tong <= 0) return '—';
  return `${(Math.round((phan / tong) * 1000) / 10).toLocaleString('vi-VN')}%`;
}

/**
 * Ngày giờ ISO -> "20/05/2025 10:30". Thiếu hoặc hỏng -> "—".
 *
 * Chuỗi CHỈ CÓ NGÀY ("2026-08-18") thì hiện ngày thôi: tự thêm "00:00" là bịa ra một
 * giờ mà nguồn không hề nói.
 */
export function ngayGioVN(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  if (/^\d{4}-\d{2}-\d{2}$/.test(iso)) return d.toLocaleDateString('vi-VN');
  return d.toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Danh sách số trang cần vẽ: `[1, '…', 4, 5, 6, '…', 20]`.
 * Luôn có trang đầu, trang cuối và hai trang quanh trang hiện tại.
 */
export function danhSachTrang(trang: number, tongTrang: number): Array<number | '…'> {
  if (tongTrang <= 7) return Array.from({ length: tongTrang }, (_, i) => i + 1);
  const giu = new Set([1, tongTrang, trang - 1, trang, trang + 1]);
  const ket: Array<number | '…'> = [];
  let truoc = 0;
  for (let i = 1; i <= tongTrang; i += 1) {
    if (!giu.has(i)) continue;
    if (i - truoc > 1) ket.push('…');
    ket.push(i);
    truoc = i;
  }
  return ket;
}
