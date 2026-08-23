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
import { UserSessionProvider } from '@/entities/user';
import { LanguageProvider } from '@/shared/i18n';

export function RootLayout() {
  // Provider bọc TOÀN BỘ route: trang đăng nhập và các trang khác là route ANH EM, không
  // có cha chung nào khác để chia sẻ state phiên. Nó chỉ đọc token trong storage lúc dựng
  // - không gọi mạng, nên trang chưa cần tài khoản cũng không tốn gì.
  // Ngôn ngữ bọc NGOÀI phiên đăng nhập: chữ trên trang đăng nhập cũng phải dịch được,
  // mà lúc đó chưa có phiên nào cả.
  return (
    <LanguageProvider>
      <UserSessionProvider>
        <Outlet />
      </UserSessionProvider>
    </LanguageProvider>
  );
}
