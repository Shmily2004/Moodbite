/**
 * Logo MoodBite — component DÙNG CHUNG cho mọi layout (đăng nhập, header, trang lỗi…).
 *
 * VÌ SAO LÀ COMPONENT CHỨ KHÔNG PHẢI CHÉP THẺ <img> Ở TỪNG TRANG: bộ nhận diện chỉ có
 * MỘT bản. Đổi file logo thì sửa đúng một dòng ở `shared/config/images.ts`, không phải
 * đi tìm mười chỗ. Đây cũng là lý do KHÔNG vẽ lại logo bằng CSS/SVG theo ảnh mẫu
 * thiết kế — ảnh mẫu dùng bản logo CŨ (chủ dự án chốt 2026-08-21).
 *
 * Ảnh thiếu hoặc hỏng thì hiện chữ "MoodBite" thay thế, không để ô ảnh vỡ.
 */
import { useState } from 'react';
import { ANH_GIAO_DIEN } from '../config';

export interface BrandLogoProps {
  /**
   * Chiều cao hiển thị — nhận CHUỖI CSS (`'64px'`, `'clamp(...)'`) chứ không phải số,
   * để nơi dùng có thể cho logo co theo màn hình. Bỏ trống thì dùng cỡ chuẩn.
   */
  height?: string;
  className?: string;
}

/**
 * KHÔNG phải một con số cố định — logo co theo bề ngang màn hình.
 *
 * Con số lấy từ chính bản thiết kế chứ không ước lượng: trong `design/Login - register.png`,
 * logo rộng bằng **0,74 lần bề ngang thẻ form**. Thẻ form của ta rộng tối đa 430px, nên
 * logo rộng ~318px, tức CAO ~160px (tỉ lệ ảnh 226×114 ≈ 1,98).
 *
 * Đã thử 34px → 46px → 64px, cả ba lần chủ dự án đều nói còn quá bé. Đây là logo có 3
 * tầng (mascot + tên + khẩu hiệu), nó đóng vai một khối hình chứ không phải cái nhãn nhỏ
 * ở góc. Muốn đổi thì đổi ở ĐÂY, đừng đặt chiều cao rải rác trong từng trang.
 */
const DEFAULT_HEIGHT = 'clamp(72px, 11vw, 158px)';

export function BrandLogo({ height = DEFAULT_HEIGHT, className }: BrandLogoProps) {
  const anh = ANH_GIAO_DIEN.logo;
  const [anhHong, setAnhHong] = useState(false);

  const classes = ['brand-logo', className].filter(Boolean).join(' ');

  if (!anh || anhHong) {
    // Bản thay thế bằng chữ: vẫn đọc được, vẫn nhận ra thương hiệu.
    return (
      <span
        className={`${classes} brand-logo--text`}
        // Chữ cao khoảng một nửa khung logo thì nhìn cân với bản có ảnh.
        style={{ fontSize: `calc(${height} * 0.42)` }}
      >
        Mood<span className="brand-logo__accent">Bite</span>
      </span>
    );
  }

  return (
    <img
      className={classes}
      src={anh.src}
      alt={anh.alt}
      // Khai width/height GỐC để trình duyệt chừa sẵn chỗ -> trang không nhảy khi ảnh tải xong.
      width={anh.width}
      height={anh.height}
      style={{ height, width: 'auto' }}
      onError={() => setAnhHong(true)}
    />
  );
}
