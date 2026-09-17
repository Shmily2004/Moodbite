/**
 * Hình học của biểu đồ radar — thuần toán, KHÔNG phải quy tắc nghiệp vụ.
 *
 * Tự tính bằng SVG thay vì thêm thư viện biểu đồ (Recharts ~100KB): cả biểu đồ chỉ là vài
 * đa giác đồng tâm, không đáng một phụ thuộc nặng.
 */

export interface Diem {
  x: number;
  y: number;
}

/**
 * Toạ độ điểm thứ `i` trên `soTruc` trục, cách tâm `tyLe × banKinh`.
 * Trục đầu tiên chỉ THẲNG LÊN (−90°), các trục sau xoay theo chiều kim đồng hồ.
 */
export function diemTrenTruc(
  i: number,
  soTruc: number,
  tyLe: number,
  tam: number,
  banKinh: number,
): Diem {
  const goc = -Math.PI / 2 + (2 * Math.PI * i) / soTruc;
  return {
    x: tam + Math.cos(goc) * banKinh * tyLe,
    y: tam + Math.sin(goc) * banKinh * tyLe,
  };
}

/** Chuỗi `points` cho `<polygon>`. Làm tròn 1 chữ số để DOM gọn và test so được. */
export function chuoiDiem(diem: Diem[]): string {
  return diem.map((d) => `${d.x.toFixed(1)},${d.y.toFixed(1)}`).join(' ');
}

/** Căn chữ nhãn theo phía của điểm: bên trái tâm thì neo phải, và ngược lại. */
export function neoChu(x: number, tam: number): 'start' | 'middle' | 'end' {
  if (Math.abs(x - tam) < 1) return 'middle';
  return x < tam ? 'end' : 'start';
}
