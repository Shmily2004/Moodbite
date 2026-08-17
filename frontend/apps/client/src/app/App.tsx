/**
 * Tầng `app` — khởi tạo ứng dụng.
 *
 * Chỉ làm đúng một việc: dựng router từ danh sách route đã khai ở `routes.tsx`.
 * Khung giao diện (header/footer) nằm ở `layout/RootLayout.tsx`.
 */
import { RouterProvider, createBrowserRouter } from 'react-router-dom';
import { routes } from './routes';
import './styles.css';

const router = createBrowserRouter(routes);

export function App() {
  return <RouterProvider router={router} />;
}
