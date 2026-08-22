/**
 * Câu khẩu hiệu "Ăn gì ở Hà Nội, tùy mood của bạn." — ẢNH lấy từ bộ nhận diện.
 *
 * VÌ SAO KHÔNG DỰNG BẰNG CHỮ: câu này dùng bộ chữ riêng của bản thiết kế (kể cả chữ
 * "mood" viết tay). Dựng bằng chữ hệ thống thì sai nét, chủ dự án đã nhận xét là trông
 * "xượng"; dựng bằng webfont thì phải ĐOÁN đúng font và tải thêm từ mạng ngoài.
 *
 * BÙ LẠI PHẦN MẤT MÁT: chữ trong ảnh thì không đọc được bằng máy, nên `alt` phải là
 * ĐÚNG câu đó (khai ở `shared/config/images.ts`) — trình đọc màn hình vẫn nghe được
 * nguyên câu, và công cụ tìm kiếm vẫn hiểu.
 *
 * Thiếu file ảnh thì lui về bản dựng bằng chữ: xấu hơn nhưng vẫn đọc được, còn hơn để
 * trang trống trơn không biết đây là cái gì.
 */
import { useState } from 'react';
import { ANH_GIAO_DIEN } from '../config';

export function Slogan({ className }: { className?: string }) {
  const anh = ANH_GIAO_DIEN.slogan;
  const [anhHong, setAnhHong] = useState(false);

  const classes = ['slogan', className].filter(Boolean).join(' ');

  if (!anh || anhHong) {
    return (
      <span className={`${classes} slogan--text`}>
        Ăn gì ở Hà Nội,
        <br />
        tùy <em className="slogan__accent">mood</em> của bạn.
      </span>
    );
  }

  return (
    <img
      className={classes}
      src={anh.src}
      alt={anh.alt}
      width={anh.width}
      height={anh.height}
      onError={() => setAnhHong(true)}
    />
  );
}
