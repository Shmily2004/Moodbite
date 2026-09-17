/**
 * DẢI MỜI ĐĂNG KÝ "Muốn MoodBite hiểu bạn hơn?" — tách khỏi `HomePage` (2026-09-16) để
 * trang `/recommend` dùng lại được. Trước đó nó là JSX viết thẳng trong trang chủ; chép
 * sang trang thứ hai là hai bản phải sửa cùng lúc mỗi lần đổi câu chữ.
 *
 * CHỈ DÀNH CHO KHÁCH — trang gọi tự quyết có đặt hay không (widget không đọc phiên đăng
 * nhập, để test/trang nào cũng dựng được mà không cần provider).
 *
 * Nội dung nói đúng thứ đăng ký ĐEM LẠI THẬT (lưu mood, gợi ý theo lựa chọn), không hứa
 * "98% phù hợp" hay "dành riêng cho bạn" — những thứ chưa có ở backend.
 */
import { Link } from 'react-router-dom';
import { ANH_GIAO_DIEN, ROUTES } from '@/shared/config';
import { IconTarget } from '@/shared/ui';
import { useT } from '@/shared/i18n';

export interface SignupCtaProps {
  /** Nút "Khám phá ngay": mỗi trang cuộn tới khối kết quả của chính nó. */
  onExplore: () => void;
}

export function SignupCta({ onExplore }: SignupCtaProps) {
  const t = useT();

  return (
    <section className="cta">
      {ANH_GIAO_DIEN.mascot && (
        <img
          className="cta__mascot"
          src={ANH_GIAO_DIEN.mascot.src}
          alt=""
          width={ANH_GIAO_DIEN.mascot.width}
          height={ANH_GIAO_DIEN.mascot.height}
          aria-hidden="true"
        />
      )}
      <div className="cta__text">
        <p className="cta__title">
          <IconTarget /> {t('cta.title')}
        </p>
        <p className="cta__sub">{t('cta.sub')}</p>
      </div>
      <div className="cta__actions">
        <button type="button" className="btn" onClick={onExplore}>
          {t('cta.explore')}
        </button>
        <Link className="btn btn--accent" to={ROUTES.register}>
          {t('cta.register')}
        </Link>
      </div>
    </section>
  );
}
