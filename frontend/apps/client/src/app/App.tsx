/**
 * Tầng `app` — khởi tạo ứng dụng.
 *
 * Chỉ làm đúng một việc: dựng router từ danh sách route đã khai ở `routes.tsx`.
 * Khung giao diện (header/footer) nằm ở `layout/RootLayout.tsx`.
 */
import { RouterProvider, createBrowserRouter } from 'react-router-dom';
import { routes } from './routes';
import './styles.css';
// Tách theo VIỆC chứ không theo trang: `brand.css` là màu + mảnh dùng lại ở mọi layout,
// `auth.css` là bố cục riêng của nhóm trang tài khoản. Thêm layout mới thì thêm một file
// ở `app/styles/` và một dòng import ở đây - đừng nhồi tiếp vào `styles.css`.
import './styles/brand.css';
import './styles/auth.css';
import './styles/home.css';
import './styles/account.css';
import './styles/my-places.css';

// Bật sớm hai hành vi của React Router v7 (2026-10-02): hết cảnh báo "Future Flag" ở MỌI
// trang, và lên v7 sau này không đổi hành vi bất ngờ. Route `*` duy nhất là trang 404,
// không có link tương đối bên trong, nên `v7_relativeSplatPath` không ảnh hưởng gì.
const router = createBrowserRouter(routes, { future: { v7_relativeSplatPath: true } });

export function App() {
  return <RouterProvider router={router} future={{ v7_startTransition: true }} />;
}
