/**
 * Gốc app quản trị — chỉ dựng router từ danh sách route đã khai ở `routes.tsx`.
 *
 * Khung giao diện nằm ở `layout/AdminLayout.tsx`, chốt chặn đăng nhập ở
 * `layout/RequireAuth.tsx`.
 */
import { RouterProvider, createBrowserRouter } from 'react-router-dom';
import { routes } from './routes';
import './styles.css';

const router = createBrowserRouter(routes);

export function App() {
  return <RouterProvider router={router} />;
}
