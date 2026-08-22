/**
 * Bộ biểu tượng dạng SVG nội tuyến.
 *
 * VÌ SAO KHÔNG DÙNG THƯ VIỆN ICON: mỗi thư viện là thêm một phụ thuộc npm và vài trăm KB
 * cho đúng bốn hình. VÌ SAO KHÔNG DÙNG EMOJI: emoji mỗi hệ điều hành vẽ một kiểu, và
 * không đổi màu theo giao diện được.
 *
 * Mọi icon dùng `stroke="currentColor"` nên nó tự ăn màu chữ của chỗ đang đặt — nền
 * sáng hay nền tối đều đúng, không phải khai màu hai lần.
 *
 * `aria-hidden` cho TẤT CẢ: đây là hình trang trí cạnh một nhãn có sẵn. Trình đọc màn
 * hình đọc nhãn là đủ; đọc thêm "hình cái khoá" chỉ gây ồn.
 */
import type { SVGProps } from 'react';

type IconProps = SVGProps<SVGSVGElement>;

function Icon({ children, ...props }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="20"
      height="20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...props}
    >
      {children}
    </svg>
  );
}

/** Người dùng — đặt trong ô "Tên đăng nhập". */
export function IconUser(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="8" r="3.5" />
      <path d="M4.5 20a7.5 7.5 0 0 1 15 0" />
    </Icon>
  );
}

/** Ổ khoá — đặt trong ô "Mật khẩu". */
export function IconLock(props: IconProps) {
  return (
    <Icon {...props}>
      <rect x="4.5" y="10.5" width="15" height="9.5" rx="2.5" />
      <path d="M8 10.5V7.5a4 4 0 0 1 8 0v3" />
    </Icon>
  );
}

/** Con mắt — nút "hiện mật khẩu". */
export function IconEye(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z" />
      <circle cx="12" cy="12" r="3" />
    </Icon>
  );
}

/** Con mắt bị gạch — nút "ẩn mật khẩu". */
export function IconEyeOff(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M9.9 5.8A9.6 9.6 0 0 1 12 5.5c6 0 9.5 6.5 9.5 6.5a17 17 0 0 1-3.3 4" />
      <path d="M6.4 7.6A16.8 16.8 0 0 0 2.5 12S6 18.5 12 18.5c1.6 0 3-.5 4.2-1.1" />
      <path d="M10 10a2.8 2.8 0 0 0 4 4" />
      <path d="m3.5 3.5 17 17" />
    </Icon>
  );
}

/** Phong bì thư — đặt trong ô "Email". */
export function IconMail(props: IconProps) {
  return (
    <Icon {...props}>
      <rect x="3" y="5.5" width="18" height="13" rx="2.5" />
      <path d="m3.6 7 7.3 5.4a2 2 0 0 0 2.2 0L20.4 7" />
    </Icon>
  );
}

/** Trái tim — vế phải của nhãn "Made for Hà Nội!". */
export function IconHeart(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 20s-7-4.4-7-9.2A4 4 0 0 1 12 8a4 4 0 0 1 7 2.8C19 15.6 12 20 12 20Z" />
    </Icon>
  );
}

/** Ghim bản đồ — dùng ở nhãn "Made for Hà Nội!". */
export function IconPin(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 21s6.5-6 6.5-10.5a6.5 6.5 0 1 0-13 0C5.5 15 12 21 12 21Z" />
      <circle cx="12" cy="10.5" r="2.5" />
    </Icon>
  );
}
