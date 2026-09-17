/**
 * Các NẤC của thanh trượt bán kính (thay ô chọn 2/5/10/20 km, 2026-09-16).
 *
 * Bản thiết kế `design/Filler.png` vẽ thanh trượt 1 · 3 · 5 · 10 km. Giữ đúng bốn nấc đó,
 * THÊM hai nấc mà bản ô chọn cũ đã có và người dùng đang dùng được:
 *   - 20 km          : nút "Mở rộng 20 km" ở trang tìm kiếm vẫn dẫn tới mức này.
 *   - Không giới hạn : `null`, gửi lên là tắt lọc khoảng cách.
 * Bỏ một nấc đang dùng được chỉ để giống ảnh là thu hẹp tính năng mà không ai yêu cầu.
 *
 * Backend nhận mọi số trong (0, 100] (`DishSuggestRequest.max_distance_km`, gt=0, le=100)
 * và `null`, nên cả sáu nấc đều hợp lệ.
 */
export const NAC_KHOANG_CACH: ReadonlyArray<number | null> = [1, 3, 5, 10, 20, null];

/**
 * Vị trí trên thanh trượt cho một bán kính bất kỳ.
 *
 * Bán kính có thể KHÔNG trùng nấc nào — "Ăn gần đây" ở trang chủ đặt 2 km, hoặc URL cũ
 * `?km=2`. Khi đó đặt con trượt ở nấc gần nhất để nhìn, nhưng KHÔNG ghi đè giá trị thật:
 * chỉ khi người dùng kéo thì mới đổi. Nhãn bên cạnh vẫn hiện đúng "2 km".
 */
export function viTriNac(km: number | null | undefined): number {
  if (km === null) return NAC_KHOANG_CACH.length - 1;
  if (km === undefined) return NAC_KHOANG_CACH.indexOf(10);

  let tot_nhat = 0;
  NAC_KHOANG_CACH.forEach((nac, i) => {
    if (nac === null) return;
    const hien = NAC_KHOANG_CACH[tot_nhat] as number;
    if (Math.abs(nac - km) < Math.abs(hien - km)) tot_nhat = i;
  });
  return tot_nhat;
}

export function giaTriNac(viTri: number): number | null {
  const i = Math.min(Math.max(Math.round(viTri), 0), NAC_KHOANG_CACH.length - 1);
  return NAC_KHOANG_CACH[i];
}
