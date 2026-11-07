/**
 * ĐƯỜNG DẪN của khu quản trị — gắn vào router của app người dùng dưới `/quan-tri`.
 *
 * Từ 2026-11-01 khu quản trị KHÔNG còn là app riêng: app người dùng import mảng này và đặt
 * vào router của mình. Không có `createBrowserRouter` ở đây nữa.
 *
 * Cấu trúc lồng nhau có chủ đích, đọc từ ngoài vào trong:
 *
 *   /quan-tri                     AdminSessionProvider  ← phiên quản trị dùng chung
 *   └── RequireAuth               ← chưa có token quản trị thì đá về /login
 *       └── AdminLayout           ← khung: thanh trên + điều hướng + đăng xuất
 *           ├── /quan-tri             TỔNG QUAN
 *           ├── /quan-tri/quan-an     danh sách quán
 *           ├── /quan-tri/mon-an      danh mục món
 *           ├── /quan-tri/mon-an/:id  chi tiết một món
 *           ├── /quan-tri/chat-luong  chất lượng dữ liệu
 *           ├── /quan-tri/can-xu-ly   inbox vấn đề dữ liệu
 *           ├── /quan-tri/goi-y       năm lớp mô hình
 *           ├── /quan-tri/nhat-ky     nhật ký hoạt động
 *           ├── /quan-tri/cai-dat     cấu hình (chỉ đọc)
 *           └── *                     404 (vẫn nằm TRONG khung)
 *
 * THÊM TRANG MỚI:
 *   1. Tạo `pages/<ten-trang>/`
 *   2. Thêm đường dẫn vào `shared/config/routes.ts` (nhớ tiền tố `/quan-tri`)
 *   3. Thêm một dòng vào `children` của `AdminLayout` bên dưới
 *   4. Thêm `<NavLink>` vào `AdminLayout` nếu muốn hiện trên thanh điều hướng
 */
import type { RouteObject } from 'react-router-dom';
import { AdminSessionProvider } from '@admin/features/admin-login';
import { ActivityPage } from '@admin/pages/activity';
import { DishesPage } from '@admin/pages/dishes';
import { DishDetailPage } from '@admin/pages/dish-detail';
import { IssuesPage } from '@admin/pages/issues';
import { OverviewPage } from '@admin/pages/overview';
import { QualityPage } from '@admin/pages/quality';
import { RecommendationPage } from '@admin/pages/recommendation';
import { SystemPage } from '@admin/pages/system';
import { NotFoundPage } from '@admin/pages/not-found';
import { RestaurantsPage } from '@admin/pages/restaurants';
import { ROUTES } from '@admin/shared/config';
import { AdminLayout } from './layout/AdminLayout';
import { RequireAuth } from './layout/RequireAuth';
import { SessionBoundary } from './layout/SessionBoundary';
import { RouteError } from './layout/RouteError';

/** Một route cha duy nhất: mọi thứ của khu quản trị nằm dưới `/quan-tri`. */
export const quanTriRoutes: RouteObject[] = [
  {
    path: ROUTES.overview,
    element: (
      <AdminSessionProvider>
        <SessionBoundary />
      </AdminSessionProvider>
    ),
    // Trang lỗi thay cho "Unexpected Application Error!" tiếng Anh của React Router.
    errorElement: <RouteError />,
    children: [
      {
        element: <RequireAuth />,
        children: [
          {
            element: <AdminLayout />,
            children: [
              { index: true, element: <OverviewPage /> },
              { path: ROUTES.restaurants, element: <RestaurantsPage /> },
              { path: ROUTES.dishes, element: <DishesPage /> },
              { path: ROUTES.dishDetail, element: <DishDetailPage /> },
              { path: ROUTES.quality, element: <QualityPage /> },
              { path: ROUTES.issues, element: <IssuesPage /> },
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
