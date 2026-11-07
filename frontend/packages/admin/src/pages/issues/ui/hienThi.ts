/** Nhãn + định dạng dùng chung của trang "Cần xử lý" (tách 2026-10-06 khi file trang vượt ~300 dòng). */

/** Nhãn tiếng Việt của loại đối tượng. */
export const NHAN_LOAI: Record<string, string> = {
  quan_an: 'Quán ăn',
  mon_an: 'Món ăn',
  du_lieu: 'Dữ liệu',
};

export function soVN(n: number): string {
  return n.toLocaleString('vi-VN');
}
