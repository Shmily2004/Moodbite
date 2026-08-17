/**
 * ĐĂNG KÝ ROUTE của app người dùng — nơi DUY NHẤT khai "đường dẫn nào ra trang nào".
 *
 * Tách khỏi `App.tsx` có chủ đích: `App.tsx` chỉ lo dựng router, còn danh sách route là
 * dữ liệu thuần. Nhờ vậy test có thể dựng `createMemoryRouter(routes)` để vào thẳng một
 * đường dẫn bất kỳ mà không cần trình duyệt thật.
 *
 * THÊM TRANG MỚI:
 *   1. Tạo `pages/<ten-trang>/` (có `ui/` và `index.ts`)
 *   2. Thêm một dòng vào mảng `children` bên dưới
 *   Header/footer tự có sẵn nhờ `RootLayout` — không phải chép lại.
 */
import type { RouteObject } from 'react-router-dom';
import { SearchPage } from '@/pages/search';
import { NotFoundPage } from '@/pages/not-found';
import { RootLayout } from './layout/RootLayout';

/** Đường dẫn khai ở MỘT chỗ, để không rải chuỗi '/' khắp nơi rồi gõ sai. */
export const ROUTES = {
  search: '/',
} as const;

export const routes: RouteObject[] = [
  {
    // Route cha không có `path`: nó chỉ đóng vai trò bọc layout quanh mọi trang con.
    element: <RootLayout />,
    children: [
      { index: true, element: <SearchPage /> },
      // '*' phải nằm CUỐI: react-router chọn route khớp nhất, nhưng để nhầm thứ tự
      // vẫn dễ gây hiểu lầm khi đọc.
      { path: '*', element: <NotFoundPage /> },
    ],
  },
];
