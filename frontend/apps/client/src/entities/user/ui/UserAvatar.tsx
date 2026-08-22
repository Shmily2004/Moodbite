/**
 * Ảnh đại diện. Có ảnh riêng thì hiện ảnh, chưa có thì sinh một ảnh mặc định TỪ TÊN.
 *
 * VÌ SAO SINH TỪ TÊN CHỨ KHÔNG DÙNG MỘT ẢNH XÁM CHUNG: cùng một người luôn ra cùng một
 * màu, nên nhìn quen mắt và phân biệt được tài khoản — giống hệt cách `RestaurantThumb`
 * xử lý 78% quán không có ảnh. Không tốn gì, không phụ thuộc mạng.
 *
 * VÌ SAO KHÔNG DÙNG DỊCH VỤ AVATAR NGOÀI (Gravatar, DiceBear, ui-avatars...): gửi tên
 * hoặc email người dùng sang máy chủ bên thứ ba chỉ để lấy một hình tròn là rò rỉ dữ liệu
 * cá nhân không cần thiết, và trang sẽ hỏng khi mất mạng.
 */
import type { CSSProperties } from 'react';

export interface UserAvatarProps {
  /** Tên hiển thị hoặc tên đăng nhập — dùng để sinh chữ cái và màu. */
  name: string | null;
  /** Data URL ảnh người dùng tự tải lên. `null` = dùng ảnh mặc định. */
  src?: string | null;
  /** Cạnh của hình vuông, tính bằng px. */
  size?: number;
  className?: string;
}

/** Băm tên -> góc màu 0..359. djb2 rút gọn, đủ tản đều cho việc này. */
function hueFromName(name: string): number {
  let hash = 5381;
  for (let i = 0; i < name.length; i += 1) {
    hash = ((hash << 5) + hash + name.charCodeAt(i)) | 0;
  }
  return Math.abs(hash) % 360;
}

/** Chữ cái đầu của tên. Tên tiếng Việt có dấu vẫn hiện đúng vì lấy nguyên ký tự. */
function chuDau(name: string): string {
  const chu = name.trim();
  return chu ? chu[0].toUpperCase() : '?';
}

export function UserAvatar({ name, src, size = 40, className }: UserAvatarProps) {
  const classes = ['avatar', className].filter(Boolean).join(' ');
  const style = { width: size, height: size } as CSSProperties;

  if (src) {
    return (
      <img
        className={classes}
        src={src}
        // Ảnh đại diện là TRANG TRÍ cạnh tên người dùng vốn đã hiện ngay bên cạnh; đọc
        // thêm "ảnh đại diện của Minh Anh" chỉ làm ồn cho người dùng trình đọc màn hình.
        alt=""
        style={style}
      />
    );
  }

  const ten = name ?? '';
  return (
    <span
      className={`${classes} avatar--chu`}
      style={{ ...style, '--avatar-h': hueFromName(ten), fontSize: size * 0.42 } as CSSProperties}
      aria-hidden="true"
    >
      {chuDau(ten)}
    </span>
  );
}
