/**
 * ĐĂNG KÝ ROUTE của app quản trị.
 *
 * Cấu trúc lồng nhau có chủ đích, đọc từ ngoài vào trong:
 *
 *   AdminSessionProvider     ← phiên đăng nhập, dùng chung cho MỌI route
 *   ├── /login               ← công khai (chưa đăng nhập cũng vào được)
 *   └── RequireAuth          ← chốt chặn: chưa đăng nhập thì đá về /login
 *       └── AdminLayout      ← khung: thanh trên + điều hướng + nút đăng xuất
 *           ├── /            ← TỔNG QUAN (số liệu vận hành)
 *           ├── /quan-an     ← danh sách quán
 *           ├── /mon-an      ← danh mục món
 *           ├── /goi-y       ← năm lớp mô hình
 *           ├── /nhat-ky     ← nhật ký hoạt động
 *           ├── /cai-dat     ← cấu hình (chỉ đọc)
 *           └── *            ← 404 (vẫn nằm TRONG khung)
 *
 * Nhờ đặt `RequireAuth` ở tầng ngoài, THÊM TRANG MỚI là tự động được bảo vệ — không thể
 * quên. Đây là bản song song ở frontend của việc backend gắn xác thực ở CẤP ROUTER.
 *
 * THÊM TRANG MỚI:
 *   1. Tạo `pages/<ten-trang>/`
 *   2. Thêm đường dẫn vào `shared/config/routes.ts`
 *   3. Thêm một dòng vào `children` của `AdminLayout`
 *   4. Thêm `<NavLink>` vào `AdminLayout` nếu muốn hiện trên thanh điều hướng
 */
import type { RouteObject } from 'react-router-dom';
import { AdminSessionProvider } from '@/features/admin-login';
import { LoginPage } from '@/pages/login';
import { NotFoundPage } from '@/pages/not-found';
import { ActivityPage } from '@/pages/activity';
import { DishesPage } from '@/pages/dishes';
import { OverviewPage } from '@/pages/overview';
import { RecommendationPage } from '@/pages/recommendation';
import { SystemPage } from '@/pages/system';
import { RestaurantsPage } from '@/pages/restaurants';
import { ROUTES } from '@/shared/config';
import { AdminLayout } from './layout/AdminLayout';
import { RequireAuth } from './layout/RequireAuth';
import { SessionBoundary } from './layout/SessionBoundary';

export const routes: RouteObject[] = [
  {
    element: (
      <AdminSessionProvider>
        <SessionBoundary />
      </AdminSessionProvider>
    ),
    children: [
      { path: ROUTES.login, element: <LoginPage /> },
      {
        element: <RequireAuth />,
        children: [
          {
            element: <AdminLayout />,
            children: [
              { index: true, element: <OverviewPage /> },
              { path: ROUTES.restaurants, element: <RestaurantsPage /> },
              { path: ROUTES.dishes, element: <DishesPage /> },
              { path: ROUTES.recommendation, element: <RecommendationPage /> },
              { path: ROUTES.activity, element: <ActivityPage /> },
              { path: ROUTES.system, element: <SystemPage /> },
              { path: '*', element: <NotFoundPage /> },
            ],
          },
        ],
      },
    ],
  },
];
