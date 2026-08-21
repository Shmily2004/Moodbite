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
  /** Chiều cao hiển thị, tính bằng px. Chiều rộng tự co theo tỉ lệ gốc. */
  height?: number;
  className?: string;
}

/**
 * 64px. Logo có 3 tầng (hình mascot + tên + khẩu hiệu "Find Your Food, Match Your Mood"),
 * nên nó cần CAO GẤP ĐÔI một logo chỉ có chữ mới cân với phần còn lại của trang.
 *
 * Đã thử 34px rồi 46px và chụp màn hình thật ở 1440px: cả hai đều bị chủ dự án nhận xét
 * là quá bé, và ở 46px dòng khẩu hiệu vẫn chỉ là một vệt xám. Đừng hạ xuống nữa.
 */
const DEFAULT_HEIGHT_PX = 64;

export function BrandLogo({ height = DEFAULT_HEIGHT_PX, className }: BrandLogoProps) {
  const anh = ANH_GIAO_DIEN.logo;
  const [anhHong, setAnhHong] = useState(false);

  const classes = ['brand-logo', className].filter(Boolean).join(' ');

  if (!anh || anhHong) {
    // Bản thay thế bằng chữ: vẫn đọc được, vẫn nhận ra thương hiệu.
    return (
      <span className={`${classes} brand-logo--text`} style={{ fontSize: height * 0.52 }}>
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
