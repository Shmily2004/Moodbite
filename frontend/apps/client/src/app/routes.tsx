/**
 * ĐĂNG KÝ ROUTE của app người dùng — nơi DUY NHẤT khai "đường dẫn nào ra trang nào".
 *
 * Tách khỏi `App.tsx` có chủ đích: `App.tsx` chỉ lo dựng router, còn danh sách route là
 * dữ liệu thuần. Nhờ vậy test có thể dựng `createMemoryRouter(routes)` để vào thẳng một
 * đường dẫn bất kỳ mà không cần trình duyệt thật.
 *
 * LUỒNG CHÍNH (chốt với chủ dự án 2026-08-18):
 *     /              chọn bộ lọc  -> danh sách MÓN
 *     /dishes/:id    thành phần món -> quán gần đây -> review
 *
 * `/search` là luồng CŨ (gõ câu tự nhiên rồi ra thẳng danh sách quán). Giữ lại chứ
 * không xoá, vì nó vẫn chạy tốt và là USP "tìm bằng câu tự nhiên" của đề án - xem
 * CLAUDE.md mục 8: xoá code đang chạy được thì phải hỏi trước.
 *
 * THÊM TRANG MỚI:
 *   1. Tạo `pages/<ten-trang>/` (có `ui/` và `index.ts`)
 *   2. Thêm một dòng vào mảng `children` bên dưới
 *   Header/footer tự có sẵn nhờ `RootLayout` — không phải chép lại.
 */
import type { RouteObject } from 'react-router-dom';
import { Navigate, useLocation, useParams } from 'react-router-dom';
import { HomePage } from '@/pages/home';
import { DishPage } from '@/pages/dish';
import { SearchPage } from '@/pages/search';
import { LoginPage } from '@/pages/login';
import { RegisterPage } from '@/pages/register';
import { ForgotPasswordPage } from '@/pages/forgot-password';
import { ResetPasswordPage } from '@/pages/reset-password';
import { VerifyEmailPage } from '@/pages/verify-email';
import { AccountPage } from '@/pages/account';
import { NotFoundPage } from '@/pages/not-found';
import { DUONG_DAN_CU, ROUTES } from '@/shared/config';
import { RootLayout } from './layout/RootLayout';

/** Đường dẫn khai ở `shared/config/routes.ts` để mọi tầng FSD đều với tới được. */
export { ROUTES };

/**
 * Chuyển hướng từ đường dẫn cũ sang đường dẫn mới.
 *
 * Giữ NGUYÊN query string (`?token=…`) và thay các tham số động (`:dishId`) bằng giá trị
 * thật. `replace` để nút Back không kẹt trong vòng lặp chuyển hướng.
 */
function ChuyenHuong({ den }: { den: string }) {
  const params = useParams();
  const location = useLocation();

  const dich = Object.entries(params).reduce(
    (duong, [ten, gia_tri]) => duong.replace(`:${ten}`, gia_tri ?? ''),
    den,
  );

  return <Navigate to={`${dich}${location.search}`} replace />;
}

export const routes: RouteObject[] = [
  {
    // Route cha không có `path`: nó chỉ đóng vai trò bọc layout quanh mọi trang con.
    element: <RootLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: ROUTES.dish, element: <DishPage /> },
      // Đăng nhập/đăng ký là TUỲ CHỌN: không có route guard nào bắt qua đây trước.
      { path: ROUTES.login, element: <LoginPage /> },
      { path: ROUTES.register, element: <RegisterPage /> },
      { path: ROUTES.forgotPassword, element: <ForgotPasswordPage /> },
      { path: ROUTES.resetPassword, element: <ResetPasswordPage /> },
      { path: ROUTES.verifyEmail, element: <VerifyEmailPage /> },
      { path: ROUTES.account, element: <AccountPage /> },
      // Luồng cũ: tìm quán bằng câu tự nhiên.
      { path: ROUTES.search, element: <SearchPage /> },
      // Đường dẫn CŨ (tiếng Việt) -> chuyển hướng sang đường mới, GIỮ nguyên query string.
      // Quan trọng nhất là `/dat-lai-mat-khau?token=…`: link đó đã nằm trong hộp thư người
      // dùng từ trước khi đổi, xoá thẳng là thư cũ chết.
      ...Object.entries(DUONG_DAN_CU).map(([cu, moi]) => ({
        path: cu,
        element: <ChuyenHuong den={moi} />,
      })),
      // '*' phải nằm CUỐI: react-router chọn route khớp nhất, nhưng để nhầm thứ tự
      // vẫn dễ gây hiểu lầm khi đọc.
      { path: '*', element: <NotFoundPage /> },
    ],
  },
];
