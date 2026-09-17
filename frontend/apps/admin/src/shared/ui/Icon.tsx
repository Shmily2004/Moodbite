/**
 * Bộ biểu tượng SVG NỘI TUYẾN cho khung quản trị.
 *
 * Không dùng emoji (hiển thị khác nhau trên mỗi hệ điều hành, và trình đọc màn hình đọc
 * to tên emoji) và không thêm thư viện icon (vài chục KB cho chục hình). Nét vẽ theo
 * `currentColor` nên tự đổi màu theo mục menu đang chọn và theo chế độ tối.
 *
 * Luôn `aria-hidden`: biểu tượng đi kèm chữ, chữ mới là tên của nút/link.
 */
import type { ReactElement } from 'react';

export type TenIcon =
  | 'tong-quan'
  | 'mon-an'
  | 'quan-an'
  | 'chat-luong'
  | 'can-xu-ly'
  | 'goi-y'
  | 'nhat-ky'
  | 'cai-dat'
  | 'mui-ten-trai'
  | 'tai-xuong'
  | 'canh-bao';

const HINH: Record<TenIcon, ReactElement> = {
  'tong-quan': <path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z" />,
  'mon-an': (
    <>
      <path d="M3 13h18a9 9 0 0 1-18 0Z" />
      <path d="M12 4v4M8 5.5l1 2.5M16 5.5l-1 2.5" />
    </>
  ),
  'quan-an': (
    <>
      <path d="M4 10v10h16V10" />
      <path d="M3 10 5 4h14l2 6a3 3 0 0 1-6 0 3 3 0 0 1-6 0 3 3 0 0 1-6 0Z" />
      <path d="M10 20v-5h4v5" />
    </>
  ),
  'chat-luong': (
    <>
      <path d="M12 3 4 6v6c0 4.5 3.4 8 8 9 4.6-1 8-4.5 8-9V6z" />
      <path d="m9 12 2 2 4-4" />
    </>
  ),
  'can-xu-ly': (
    <>
      <path d="M12 3 2 20h20Z" />
      <path d="M12 10v4M12 17h.01" />
    </>
  ),
  'goi-y': (
    <>
      <path d="M9 18h6M10 21h4" />
      <path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3Z" />
    </>
  ),
  'nhat-ky': (
    <>
      <path d="M6 3h9l4 4v14H6z" />
      <path d="M9 12h7M9 16h7M9 8h3" />
    </>
  ),
  'cai-dat': (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1" />
    </>
  ),
  'mui-ten-trai': <path d="M19 12H5M11 6l-6 6 6 6" />,
  'tai-xuong': (
    <>
      <path d="M12 4v11M7 10l5 5 5-5" />
      <path d="M5 20h14" />
    </>
  ),
  'canh-bao': (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v6M12 16.5h.01" />
    </>
  ),
};

export function Icon({ ten, className }: { ten: TenIcon; className?: string }) {
  return (
    <svg
      className={className ?? 'icon'}
      viewBox="0 0 24 24"
      width="18"
      height="18"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {HINH[ten]}
    </svg>
  );
}
