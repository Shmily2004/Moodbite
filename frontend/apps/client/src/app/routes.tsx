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
import { Suspense, lazy } from 'react';
import type { ComponentType } from 'react';
import type { RouteObject } from 'react-router-dom';
import { Navigate, useLocation, useParams } from 'react-router-dom';
import { HomePage } from '@/pages/home';
import { LoginPage } from '@/pages/login';
import { RegisterPage } from '@/pages/register';
import { ForgotPasswordPage } from '@/pages/forgot-password';
import { ResetPasswordPage } from '@/pages/reset-password';
import { VerifyEmailPage } from '@/pages/verify-email';
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

/**
 * TẢI SAU (code-splitting) cho các trang NẶNG - thêm 2026-10-02.
 *
 * Trước đó cả app là MỘT file JS 532 kB (vượt ngưỡng 500 kB Vite cảnh báo), vì bốn trang
 * này kéo theo Leaflet (bản đồ) và nhiều widget. Người mở trang chủ không cần bản đồ mà
 * vẫn phải tải hết. `taiSau` chỉ tải file của trang khi vào đúng route đó.
 * Trang chủ và các trang đăng nhập nhỏ vẫn tải ngay - đó là màn đầu tiên người ta thấy.
 */
function taiSau(nap: () => Promise<{ default: ComponentType }>) {
  const Trang = lazy(nap);
  // `React.lazy` + `Suspense` chứ KHÔNG dùng thuộc tính `lazy` của route: thuộc tính đó
  // chỉ chạy với data router, còn test dựng route bằng `useRoutes` (xem App.test.tsx - data
  // router trong jsdom vướng lỗi AbortSignal của Node). Cách này chạy được ở cả hai nơi.
  return (
    <Suspense fallback={<p className="trang-dang-tai" role="status">Đang tải trang…</p>}>
      <Trang />
    </Suspense>
  );
}

const trangMon = taiSau(() => import('@/pages/dish').then((m) => ({ default: m.DishPage })));
const trangTimKiem = taiSau(() =>
  import('@/pages/search').then((m) => ({ default: m.SearchPage })),
);
const trangGoiY = taiSau(() =>
  import('@/pages/recommend').then((m) => ({ default: m.RecommendPage })),
);
const trangTaiKhoan = taiSau(() =>
  import('@/pages/account').then((m) => ({ default: m.AccountPage })),
);
export const routes: RouteObject[] = [
  {
    // Route cha không có `path`: nó chỉ đóng vai trò bọc layout quanh mọi trang con.
    element: <RootLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: ROUTES.dish, element: trangMon },
      // Đăng nhập/đăng ký là TUỲ CHỌN: không có route guard nào bắt qua đây trước.
      { path: ROUTES.login, element: <LoginPage /> },
      { path: ROUTES.register, element: <RegisterPage /> },
      { path: ROUTES.forgotPassword, element: <ForgotPasswordPage /> },
      { path: ROUTES.resetPassword, element: <ResetPasswordPage /> },
      { path: ROUTES.verifyEmail, element: <VerifyEmailPage /> },
      { path: ROUTES.account, element: trangTaiKhoan },
      // Luồng cũ: tìm quán bằng câu tự nhiên.
      { path: ROUTES.search, element: trangTimKiem },
      { path: ROUTES.recommend, element: trangGoiY },
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
