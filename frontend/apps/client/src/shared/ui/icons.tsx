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
export function IconHeart({ filled = false, ...props }: IconProps & { filled?: boolean }) {
  // `filled` để MỘT hình dùng được cho cả hai trạng thái tim. Trước đây chỗ bấm tim viết
  // thẳng ký tự ♥/♡ — mỗi hệ điều hành vẽ một kiểu và không ăn màu theo giao diện.
  return (
    <Icon fill={filled ? 'currentColor' : 'none'} {...props}>
      <path d="M12 20s-7-4.4-7-9.2A4 4 0 0 1 12 8a4 4 0 0 1 7 2.8C19 15.6 12 20 12 20Z" />
    </Icon>
  );
}

/**
 * Dấu trang — danh sách "Đã lưu" (món tôi ĐỊNH ĂN, để dành xem sau).
 *
 * Cố ý KHÁC HẲN hình trái tim: hai danh sách tách bạch từ 2026-08-26, và người dùng phải
 * phân biệt được hai nút chỉ bằng cách liếc qua. Hai hình na ná nhau thì việc tách danh
 * sách chẳng còn nghĩa gì.
 */
export function IconBookmark({ filled = false, ...props }: IconProps & { filled?: boolean }) {
  return (
    <Icon fill={filled ? 'currentColor' : 'none'} {...props}>
      <path d="M6.5 3.8h11a1 1 0 0 1 1 1v15.4l-6.5-4-6.5 4V4.8a1 1 0 0 1 1-1Z" />
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

/** Thư mục — mục "Bộ sưu tập của tôi" (design/profile.png, thêm 2026-09-29). */
export function IconFolder(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M3.5 7.5A1.5 1.5 0 0 1 5 6h4.2l2 2.2H19a1.5 1.5 0 0 1 1.5 1.5v8.3A1.5 1.5 0 0 1 19 19.5H5A1.5 1.5 0 0 1 3.5 18Z" />
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

/* ===========================================================================
   ICON DÙNG CHUNG (thêm 2026-08-25)
   ---------------------------------------------------------------------------
   Đợt hai của việc bỏ emoji. Rà toàn dự án còn 141 emoji ở 23 file; phần dưới
   phủ những chỗ NGƯỜI DÙNG NHÌN THẤY NHIỀU NHẤT: thanh trên, thẻ mood trang
   chủ, tab tài khoản, nút đổi giao diện.
   Lý do bỏ emoji vẫn như đã ghi ở đầu file: mỗi hệ điều hành vẽ một kiểu và
   không đổi màu theo giao diện được.
   =========================================================================== */

/** Ngôi nhà — tab "Tổng quan". */
export function IconHome(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M3.5 10.5 12 3.5l8.5 7" />
      <path d="M5.5 9.5v10h13v-10" />
      <path d="M9.5 19.5v-6h5v6" />
    </Icon>
  );
}

/** Dao & dĩa — tab "Khẩu vị", nhãn món ăn. */
export function IconDining(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M7 3.5v7a2 2 0 0 0 4 0v-7M9 10.5v10" />
      <path d="M16.5 3.5c-1.5 1.5-1.5 5 0 6.5v10.5" />
    </Icon>
  );
}

/** Đồng hồ — "xem gần đây", giờ mở cửa. */
export function IconClock(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5V12l3 2" />
    </Icon>
  );
}

/** Huy hiệu — tab "Huy hiệu". */
export function IconBadge(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="9" r="5.5" />
      <path d="M8.5 13.5 7 21l5-2.5L17 21l-1.5-7.5" />
    </Icon>
  );
}

/** Bánh răng — cài đặt. */
export function IconSettings(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2.5v2.5M12 19v2.5M4.2 6.6l2.1 1.3M17.7 16.1l2.1 1.3M4.2 17.4l2.1-1.3M17.7 7.9l2.1-1.3" />
    </Icon>
  );
}

/** Dấu tích — trạng thái đã xong. */
export function IconCheck(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M4.5 12.5 9.5 17.5 19.5 6.5" />
    </Icon>
  );
}

/** Lịch — ngày tham gia. */
export function IconCalendar(props: IconProps) {
  return (
    <Icon {...props}>
      <rect x="3.5" y="5.5" width="17" height="15" rx="2.5" />
      <path d="M3.5 10h17M8 3.5v4M16 3.5v4" />
    </Icon>
  );
}

/** Kính lúp — ô tìm kiếm. */
export function IconSearch(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="M15.5 15.5 20.5 20.5" />
    </Icon>
  );
}

/** Ba gạch — mở menu trên điện thoại. */
export function IconMenu(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M4 7h16M4 12h16M4 17h16" />
    </Icon>
  );
}

/** Dấu nhân — đóng. */
export function IconClose(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M6 6l12 12M18 6 6 18" />
    </Icon>
  );
}

/** Ngôi sao — đánh giá. Có `filled` để vẽ sao đặc. */
export function IconStar({ filled = false, ...props }: IconProps & { filled?: boolean }) {
  return (
    <Icon fill={filled ? 'currentColor' : 'none'} {...props}>
      <path d="M12 3.5l2.6 5.6 6 .8-4.4 4.2 1.1 6-5.3-2.9-5.3 2.9 1.1-6L3.4 9.9l6-.8Z" />
    </Icon>
  );
}

/** Tam giác cảnh báo — quán tạm đóng, dữ liệu thiếu. */
export function IconWarning(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 4 21 19.5H3Z" />
      <path d="M12 10v4M12 16.8h.01" />
    </Icon>
  );
}

/** La bàn — "khám phá". */
export function IconCompass(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M15.2 8.8 13.5 13.5 8.8 15.2 10.5 10.5Z" />
    </Icon>
  );
}

/** Bàn tay vẫy — lời chào ở hero. */
export function IconWave(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M8 11V6.5a1.5 1.5 0 0 1 3 0V11" />
      <path d="M11 10.5V5a1.5 1.5 0 0 1 3 0v5.5" />
      <path d="M14 10.5V7a1.5 1.5 0 0 1 3 0v7a6.5 6.5 0 0 1-13 0v-2a1.5 1.5 0 0 1 3 0" />
    </Icon>
  );
}

/** Ba chấm — nút "Xem thêm". */
export function IconMore(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="5.5" cy="12" r="1.4" fill="currentColor" />
      <circle cx="12" cy="12" r="1.4" fill="currentColor" />
      <circle cx="18.5" cy="12" r="1.4" fill="currentColor" />
    </Icon>
  );
}

/** Nhiệt kế — số đo nhiệt độ ở hero. */
export function IconThermometer(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M10 13.5V5.5a2 2 0 0 1 4 0v8a4 4 0 1 1-4 0Z" />
      <circle cx="12" cy="17" r="1.6" fill="currentColor" />
    </Icon>
  );
}

/** Mặt trời lặn — buổi chiều. */
export function IconSunset(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M2.5 18h19" />
      <path d="M6 14a6 6 0 0 1 12 0" />
      <path d="M12 9.5v-3M4.8 11.2 6.4 9.6M19.2 11.2l-1.6-1.6" />
    </Icon>
  );
}

/** Tia lấp lánh — nhãn "gợi ý cho bạn". */
export function IconSparkle(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 3.5 13.7 9l5.5 1.7-5.5 1.7L12 18l-1.7-5.6L4.8 10.7 10.3 9Z" />
      <path d="M18.5 4v3M17 5.5h3" />
    </Icon>
  );
}

/** Ngọn lửa — nhãn "phổ biến hôm nay". */
export function IconFlame(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 3.5s5.5 4.2 5.5 9a5.5 5.5 0 0 1-11 0c0-2 1-3.5 2-4.5.3 1.2 1 2 2 2 0-2.5.5-4.8 1.5-6.5Z" />
    </Icon>
  );
}

/** Bia ngắm — mục tiêu, lời kêu gọi hành động. */
export function IconTarget(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="12" r="8.5" />
      <circle cx="12" cy="12" r="4.5" />
      <circle cx="12" cy="12" r="1.2" fill="currentColor" />
    </Icon>
  );
}

/** Bản đồ gấp — hành động chỉ đường. */
export function IconMap(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M3.5 6.5 9 4.5l6 2 5.5-2v13l-5.5 2-6-2-5.5 2Z" />
      <path d="M9 4.5v13M15 6.5v13" />
    </Icon>
  );
}

/** Ngón cái — đánh giá thích. */
export function IconThumbUp(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M7 10.5 11 3.5a2 2 0 0 1 2 2v4h5.5a2 2 0 0 1 2 2.4l-1.4 6A2 2 0 0 1 17 19.5H7Z" />
      <rect x="2.5" y="10.5" width="4.5" height="9" rx="1.2" />
    </Icon>
  );
}

/** Khiên — báo quán đã đóng cửa. */
export function IconShield(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 3.5 19.5 6v6c0 4.2-3 7.3-7.5 8.5C7.5 19.3 4.5 16.2 4.5 12V6Z" />
    </Icon>
  );
}

/* ===========================================================================
   ICON LOẠI HÌNH QUÁN & MỨC CAY (thêm 2026-09-29, checklist A9)
   ---------------------------------------------------------------------------
   Đợt cuối của việc bỏ emoji. Chủ yếu phục vụ ô ảnh TỰ SINH của thẻ quán
   (`entities/restaurant/ui/RestaurantThumb.tsx`) — chỗ hiện cho ~72% số quán vì
   phần lớn quán không có ảnh thật, nên đây là emoji người dùng nhìn thấy NHIỀU
   NHẤT còn sót lại. Cùng một nét với phần trên: viewBox 24, stroke 1.7,
   `currentColor` — ô ảnh nền màu thì icon tự ăn màu trắng của ô.
   =========================================================================== */

/** Quả ớt — mức cay của món, sở thích "Ăn cay". */
export function IconChili(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M15.5 8.5c2.5 1.5 3 5 .5 8.5-2.3 3.2-7 4.5-11.5 3.5 4-1.2 6-3.8 7-7 .8-2.5 1.8-4.6 4-5Z" />
      <path d="M15.5 8.5c0-2 .8-3.5 2.5-4.5M14 8.8c.5-1 1.5-1.4 2.5-1" />
    </Icon>
  );
}

/** Tách cà phê bốc hơi — quán cà phê. */
export function IconCoffee(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M4.5 10h12v4.5a5 5 0 0 1-5 5h-2a5 5 0 0 1-5-5Z" />
      <path d="M16.5 11.5h1.5a2.5 2.5 0 0 1 0 5h-1.8" />
      <path d="M8.5 6.8c0-1 .8-1.3.8-2.3M12 6.8c0-1 .8-1.3.8-2.3" />
    </Icon>
  );
}

/** Cốc trà sữa có ống hút — quán trà / trà sữa. */
export function IconBubbleTea(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M6 8.5h12l-1.4 11.2a1.5 1.5 0 0 1-1.5 1.3H8.9a1.5 1.5 0 0 1-1.5-1.3Z" />
      <path d="M5.5 8.5h13" />
      <path d="m12.5 8.5 2-6 2.5.8" />
      <path d="M9.5 17h.01M12 18h.01M14.5 17h.01" />
    </Icon>
  );
}

/** Ổ bánh mì — quán bánh mì. */
export function IconBread(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M5.2 18.8c-1.8-1.8-.8-5.6 2.9-9.3s7.5-4.7 9.3-2.9.8 5.6-2.9 9.3-7.5 4.7-9.3 2.9Z" />
      <path d="m9.5 11 2 2M12.5 8.5l2 2M7.5 14l1.8 1.8" />
    </Icon>
  );
}

/** Miếng bánh ngọt — tiệm bánh, kem, tráng miệng. */
export function IconCake(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M3.5 19.5h17v-7l-17-4Z" />
      <path d="M3.5 13.5l17 3" />
      <path d="M15 6.5a1.5 1.5 0 1 1 3 0c0 1-1.5 2.5-1.5 2.5S15 7.5 15 6.5Z" />
    </Icon>
  );
}

/** Con cá — hải sản. */
export function IconSeafood(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M3 12c2.5-3.5 5.5-5 9-5s6 2.5 7.5 5c-1.5 2.5-4 5-7.5 5s-6.5-1.5-9-5Z" />
      <path d="M19.5 12 22 9v6Z" />
      <path d="M8 11h.01" />
    </Icon>
  );
}

/** Miếng pizza — quán pizza / Ý. */
export function IconPizza(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M12 21 3.5 5.5a18 18 0 0 1 17 0Z" />
      <path d="M5 8.2a15 15 0 0 1 14 0" />
      <path d="M11 11h.01M13.5 14.5h.01" />
    </Icon>
  );
}

/** Bánh burger — đồ ăn nhanh. */
export function IconBurger(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M4 10.5a8 6 0 0 1 16 0Z" />
      <path d="M3.5 14h17" />
      <path d="M4.5 17h15a2.5 2.5 0 0 1-2.5 2.5H7A2.5 2.5 0 0 1 4.5 17Z" />
    </Icon>
  );
}

/** Cuộn sushi (maki) — quán Nhật. */
export function IconSushi(props: IconProps) {
  return (
    <Icon {...props}>
      <ellipse cx="12" cy="8" rx="7.5" ry="3.5" />
      <path d="M4.5 8v8c0 1.9 3.4 3.5 7.5 3.5s7.5-1.6 7.5-3.5V8" />
      <ellipse cx="12" cy="8" rx="3" ry="1.3" />
    </Icon>
  );
}

/** Chiếc lá — quán chay. */
export function IconLeaf(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M5 19c0-8 5-13.5 14.5-14.5C19 14 13.5 19 5 19Z" />
      <path d="M5 19 13 11" />
    </Icon>
  );
}

/** Cốc bia — quán bia, pub, bar. */
export function IconBeer(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M5.5 7.5h10v11.5a1.5 1.5 0 0 1-1.5 1.5H7a1.5 1.5 0 0 1-1.5-1.5Z" />
      <path d="M15.5 10h2a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2h-2" />
      <path d="M5.5 7.5a2.5 2.5 0 0 1 2.5-3.5 3 3 0 0 1 5 0 2.5 2.5 0 0 1 2.5 3.5" />
      <path d="M9 11v6M12 11v6" />
    </Icon>
  );
}

/** Bát cơm vun ngọn — quán cơm. */
export function IconRiceBowl(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M3.5 12h17a8.5 8.5 0 0 1-17 0Z" />
      <path d="M6.5 12a5.5 5 0 0 1 11 0" />
    </Icon>
  );
}

// --- Đợt đối chiếu thiết kế 2026-10-02 ------------------------------------------------

/** Mũi tên trái — nút cuộn dải thẻ món. */
export function IconChevronLeft(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M14.5 6 8.5 12l6 6" />
    </Icon>
  );
}

/** Mũi tên phải — nút cuộn dải thẻ món. */
export function IconChevronRight(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M9.5 6l6 6-6 6" />
    </Icon>
  );
}

/** Bút chì — nút "Chỉnh sửa" (bản thiết kế dùng bút chì, không phải phễu lọc). */
export function IconPencil(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M4 20l1-4.5L15.5 5a2.1 2.1 0 0 1 3 3L8 18.5Z" />
      <path d="M13.5 7l3 3" />
    </Icon>
  );
}

/** Máy ảnh — nút đổi ảnh đại diện. */
export function IconCamera(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M4 8.5A1.5 1.5 0 0 1 5.5 7h2l1.5-2h6l1.5 2h2A1.5 1.5 0 0 1 20 8.5v9a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 17.5Z" />
      <circle cx="12" cy="12.5" r="3.3" />
    </Icon>
  );
}

/** Chữ i trong vòng tròn — mở phần giải thích. */
export function IconInfo(props: IconProps) {
  return (
    <Icon {...props}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 11v5M12 8h.01" />
    </Icon>
  );
}

/** Mặt tiền cửa hàng — tiêu đề danh sách quán. */
export function IconStore(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M4 9.5 5.5 4.5h13L20 9.5" />
      <path d="M4 9.5a2.7 2.7 0 0 0 5.3 0 2.7 2.7 0 0 0 5.4 0 2.7 2.7 0 0 0 5.3 0" />
      <path d="M5.5 11.5v8h13v-8M10 19.5v-4.5h4v4.5" />
    </Icon>
  );
}
