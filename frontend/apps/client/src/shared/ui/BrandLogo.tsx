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
 * Cỡ lấy từ chính bản thiết kế chứ không ước lượng: logo rộng bằng **0,71 lần bề ngang
 * thẻ form**. Thẻ form rộng tối đa 430px -> logo rộng ~305px.
 *
 * ⚠ Chiều cao đổi theo TỈ LỆ của file logo. Bản 2026-08-22 là 3:1 (2172×724) chứ không
 * còn 2:1 như bản cũ, nên cùng một bề ngang thì nay chỉ cao bằng 2/3 trước kia.
 *
 * Đo trên bản thiết kế chủ dự án gửi 2026-08-22: logo rộng 340/1456 ≈ 23% bề ngang màn
 * hình. Tỉ lệ ảnh là 3:1 nên chiều cao ≈ 23vw / 3 ≈ 7,4vw. Chặn trên 148px để trên màn
 * hình siêu rộng logo không nuốt mất nửa thanh trên.
 */
const DEFAULT_HEIGHT = 'clamp(56px, 7.4vw, 148px)';

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
