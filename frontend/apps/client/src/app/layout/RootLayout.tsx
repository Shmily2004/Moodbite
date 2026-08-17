/**
 * LAYOUT gốc — CỐ Ý rất mỏng.
 *
 * Trang chính là bản đồ tràn màn hình, nên KHÔNG có header/footer dùng chung: mọi
 * pixel chrome đều lấn vào bản đồ. Nhãn thương hiệu nổi ngay trong `SearchPage`,
 * còn ghi công OpenStreetMap do chính Leaflet vẽ (bắt buộc theo giấy phép ODbL).
 *
 * Trang phụ (404) tự dựng khung riêng bằng class `.plain`.
 */
import { Outlet } from 'react-router-dom';

export function RootLayout() {
  return <Outlet />;
}
