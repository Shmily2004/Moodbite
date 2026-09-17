/**
 * Xuất CSV PHÍA TRÌNH DUYỆT từ dữ liệu đã tải — nút "Xuất danh sách" của bản thiết kế.
 *
 * Không gọi thêm API: xuất đúng những gì người quản trị đang nhìn thấy trên màn hình.
 * Một endpoint xuất riêng sẽ có ngày trả về tập khác với bảng đang hiện (khác bộ lọc,
 * khác thời điểm) và người ta không hiểu vì sao file khác màn hình.
 */

export type OCsv = string | number | boolean | null | undefined;

/** Bọc một ô theo RFC 4180: có dấu phẩy, nháy kép hoặc xuống dòng thì đặt trong nháy. */
function boc(o: OCsv): string {
  // `null`/`undefined` thành ô RỖNG, không phải chữ "null" hay số 0 — chưa có dữ liệu
  // khác hẳn giá trị 0 (CLAUDE.md mục 4 quy tắc 1).
  if (o === null || o === undefined) return '';
  const chu = String(o);
  return /[",\r\n]/.test(chu) ? `"${chu.replace(/"/g, '""')}"` : chu;
}

export function taoCsv(tieuDe: string[], dong: OCsv[][]): string {
  return [tieuDe, ...dong].map((d) => d.map(boc).join(',')).join('\r\n');
}

/**
 * Tải file CSV về máy.
 *
 * Thêm BOM `﻿` ở đầu: không có nó, Excel trên Windows đọc UTF-8 thành mã lỗi và
 * chữ "Nghiêm trọng" biến thành "NghiÃªm trá»ng" — đúng máy của chủ dự án.
 */
export function taiCsv(tenFile: string, noiDung: string): void {
  const blob = new Blob(['﻿', noiDung], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = tenFile;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
