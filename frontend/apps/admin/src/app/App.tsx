/**
 * Gốc app quản trị — chỉ dựng router từ danh sách route đã khai ở `routes.tsx`.
 *
 * Khung giao diện nằm ở `layout/AdminLayout.tsx`, chốt chặn đăng nhập ở
 * `layout/RequireAuth.tsx`.
 */
import { RouterProvider, createBrowserRouter } from 'react-router-dom';
import { routes } from './routes';
import './styles.css';

// Bật sớm hai hành vi của React Router v7 (2026-10-02): hết cảnh báo "Future Flag" ở MỌI
// trang, và lên v7 sau này không đổi hành vi bất ngờ. Route `*` duy nhất là trang 404,
// không có link tương đối bên trong, nên `v7_relativeSplatPath` không ảnh hưởng gì.
const router = createBrowserRouter(routes, { future: { v7_relativeSplatPath: true } });

export function App() {
  return <RouterProvider router={router} future={{ v7_startTransition: true }} />;
}
