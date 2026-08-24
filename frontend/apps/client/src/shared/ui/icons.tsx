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

/* ===========================================================================
   ICON CHO BỘ LỌC MÓN (thêm 2026-08-24)
   ---------------------------------------------------------------------------
   Trước đó hàng chip lọc dùng EMOJI, đi ngược đúng lý do đã ghi ở đầu file này.
   Chủ dự án yêu cầu bỏ emoji, và với những khái niệm mà chủ dự án ĐÃ GỬI ẢNH
   (cay · thư giãn · đồ nướng · trời mưa · bia · healthy · hẹn hò) thì dùng ảnh
   đó qua `shared/config/images.ts`, KHÔNG vẽ lại ở đây.
   Phần dưới chỉ vẽ những khái niệm chưa có ảnh nào.
   =========================================================================== */

/** Mặt trời — trời nắng. */
export function IconSun(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.2 5.2l1.4 1.4M17.4 17.4l1.4 1.4M18.8 5.2l-1.4 1.4M6.6 17.4l-1.4 1.4" />
    </Icon>
  );
}

/** Mặt cười — mood "vui". */
export function IconSmile(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M8.5 14.5a4.5 4.5 0 0 0 7 0" />
      <path d="M9 9.5h.01M15 9.5h.01" />
    </Icon>
  );
}

/** Mặt buồn — mood "buồn". */
export function IconFrown(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M8.5 15.5a4.5 4.5 0 0 1 7 0" />
      <path d="M9 9.5h.01M15 9.5h.01" />
    </Icon>
  );
}

/** Bát bốc khói — đồ nóng. */
export function IconHotBowl(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M3.5 12.5h17a8.5 8.5 0 0 1-17 0Z" />
      <path d="M9 6.5c0-1 1-1.4 1-2.4M12.5 6c0-1.2 1-1.6 1-2.8M16 6.5c0-1 1-1.4 1-2.4" />
    </Icon>
  );
}

/** Bông tuyết — đồ mát. */
export function IconCold(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 2.5v19M3.8 7.2l16.4 9.6M20.2 7.2 3.8 16.8" />
      <path d="M12 6.2 10 4.4M12 6.2l2-1.8M12 17.8l-2 1.8M12 17.8l2 1.8" />
    </Icon>
  );
}

/** Bát có thìa — món nước. */
export function IconSoup(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M4 11.5h16a8 8 0 0 1-16 0Z" />
      <path d="M12 19.5v-1.2" />
      <path d="M7.5 8.5c1.5-1 3-1 4.5 0s3 1 4.5 0" />
    </Icon>
  );
}

/** Chảo — chiên rán. */
export function IconPan(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="10" cy="13" r="6" />
      <path d="M16 13h5.5" />
    </Icon>
  );
}

/** Chảo nghiêng có lửa — xào. */
export function IconStirFry(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M3.5 12.5a7 7 0 0 0 14 0Z" />
      <path d="M17.5 12.5 21 9.5" />
      <path d="M8.5 8.5c0-1.2 1.2-1.6 1.2-2.8M12 8c0-1.4 1.2-1.8 1.2-3" />
    </Icon>
  );
}

/** Nồi có hơi — hấp. */
export function IconSteam(props: IconProps) {
  return (
    <Icon {...props}>
      <rect x="4.5" y="11" width="15" height="8.5" rx="2" />
      <path d="M3 11h18" />
      <path d="M9 7.5c0-1.2 1.2-1.6 1.2-2.8M14 7.5c0-1.2 1.2-1.6 1.2-2.8" />
    </Icon>
  );
}

/** Giọt nước — luộc. */
export function IconBoil(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 3.5c3.2 3.6 5 6.1 5 8.4a5 5 0 0 1-10 0c0-2.3 1.8-4.8 5-8.4Z" />
    </Icon>
  );
}

/** Bát salad có đũa — trộn. */
export function IconMix(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M4 12.5h16a8 8 0 0 1-16 0Z" />
      <path d="M8.5 9 15 3.5M15.5 9 9 3.5" />
    </Icon>
  );
}

/** Mặt trời mọc — bữa sáng. */
export function IconSunrise(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M2.5 18h19" />
      <path d="M6 14a6 6 0 0 1 12 0" />
      <path d="M12 3.5v3M4.8 6.8l1.6 1.6M19.2 6.8l-1.6 1.6" />
    </Icon>
  );
}

/** Trăng khuyết — bữa tối. */
export function IconMoon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z" />
    </Icon>
  );
}

/** Trăng kèm sao — đêm khuya. */
export function IconNight(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M19.5 15A7.5 7.5 0 0 1 10 5.5 7.5 7.5 0 1 0 19.5 15Z" />
      <path d="M17 3.5l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7Z" />
    </Icon>
  );
}

/** Que xiên — ăn vặt. */
export function IconSnack(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M4.5 19.5 19 5" />
      <circle cx="9.5" cy="14.5" r="2.2" />
      <circle cx="14" cy="10" r="2.2" />
    </Icon>
  );
}

/** Phễu — nút mở bộ lọc. */
export function IconFilter(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M3.5 5.5h17l-6.5 7.5v6l-4 2v-8Z" />
    </Icon>
  );
}
