/**
 * ĐĂNG KÝ ROUTE của app người dùng — nơi DUY NHẤT khai "đường dẫn nào ra trang nào".
 *
 * Tách khỏi `App.tsx` có chủ đích: `App.tsx` chỉ lo dựng router, còn danh sách route là
 * dữ liệu thuần. Nhờ vậy test có thể dựng `createMemoryRouter(routes)` để vào thẳng một
 * đường dẫn bất kỳ mà không cần trình duyệt thật.
 *
 * LUỒNG CHÍNH (chốt với chủ dự án 2026-08-18):
 *     /              chọn bộ lọc  -> danh sách MÓN
 *     /mon/:dishId   thành phần món -> quán gần đây -> review
 *
 * `/tim-kiem` là luồng CŨ (gõ câu tự nhiên rồi ra thẳng danh sách quán). Giữ lại chứ
 * không xoá, vì nó vẫn chạy tốt và là USP "tìm bằng câu tự nhiên" của đề án - xem
 * CLAUDE.md mục 8: xoá code đang chạy được thì phải hỏi trước.
 *
 * THÊM TRANG MỚI:
 *   1. Tạo `pages/<ten-trang>/` (có `ui/` và `index.ts`)
 *   2. Thêm một dòng vào mảng `children` bên dưới
 *   Header/footer tự có sẵn nhờ `RootLayout` — không phải chép lại.
 */
import type { RouteObject } from 'react-router-dom';
import { HomePage } from '@/pages/home';
import { DishPage } from '@/pages/dish';
import { SearchPage } from '@/pages/search';
import { LoginPage } from '@/pages/login';
import { RegisterPage } from '@/pages/register';
import { ForgotPasswordPage } from '@/pages/forgot-password';
import { ResetPasswordPage } from '@/pages/reset-password';
import { NotFoundPage } from '@/pages/not-found';
import { ROUTES } from '@/shared/config';
import { RootLayout } from './layout/RootLayout';

/** Đường dẫn khai ở `shared/config/routes.ts` để mọi tầng FSD đều với tới được. */
export { ROUTES };

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
      // Luồng cũ: tìm quán bằng câu tự nhiên.
      { path: '/tim-kiem', element: <SearchPage /> },
      // '*' phải nằm CUỐI: react-router chọn route khớp nhất, nhưng để nhầm thứ tự
      // vẫn dễ gây hiểu lầm khi đọc.
      { path: '*', element: <NotFoundPage /> },
    ],
  },
];
