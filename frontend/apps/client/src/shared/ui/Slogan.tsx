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
 *
 * ⚠️ BẬT TIẾNG ANH THÌ LUÔN DỰNG BẰNG CHỮ. Ảnh khẩu hiệu chỉ có bản tiếng Việt; giữ ảnh
 * đó trên trang tiếng Anh sẽ thành một câu tiếng Việt to tướng giữa trang — trông như
 * lỗi. Có bản ảnh tiếng Anh thì thêm vào `design/attribute/` rồi bỏ nhánh này đi.
 */
import { useState } from 'react';
import { ANH_GIAO_DIEN } from '../config';
import { useNgonNgu } from '../i18n';

export function Slogan({ className }: { className?: string }) {
  const anh = ANH_GIAO_DIEN.slogan;
  const [anhHong, setAnhHong] = useState(false);
  const { ngonNgu, t } = useNgonNgu();

  const classes = ['slogan', className].filter(Boolean).join(' ');

  if (!anh || anhHong || ngonNgu !== 'vi') {
    return (
      <span className={`${classes} slogan--text`}>
        {t('hero.sloganLine1')}
        <br />
        {t('hero.sloganLine2a')} <em className="slogan__accent">mood</em>{' '}
        {t('hero.sloganLine2b')}
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
