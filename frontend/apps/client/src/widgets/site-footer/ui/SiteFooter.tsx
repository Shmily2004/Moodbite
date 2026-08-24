/**
 * CHÂN TRANG dùng chung.
 *
 * VÌ SAO CẦN — HAI LÝ DO, lý do thứ hai mới là lý do bắt buộc:
 *
 * 1. Chủ dự án chỉ ra 2026-08-24: mọi web cùng loại (Foody, Anzi, STUDY4) đều có chân
 *    trang, còn MoodBite thì trang cứ hết đột ngột.
 *
 * 2. ⚠️ GHI CÔNG NGUỒN DỮ LIỆU LÀ NGHĨA VỤ THEO GIẤY PHÉP, không phải cho đẹp.
 *    Trước hôm nay, ghi công OpenStreetMap CHỈ xuất hiện trên bản đồ Leaflet ở trang
 *    `/search` — do chính Leaflet vẽ ra. Nhưng dữ liệu quán được dùng ở KHẮP app (trang
 *    chủ, trang món, gợi ý), và ảnh món thì lấy từ Wikipedia/Wikimedia Commons. Cả ba
 *    giấy phép dưới đây đều đòi ghi công:
 *        OpenStreetMap  — ODbL 1.0
 *        Overture Maps  — CDLA-Permissive-2.0
 *        Wikipedia/Commons — CC BY-SA
 *    Thiếu ghi công là dùng sai giấy phép, và đây đúng chỗ dễ bị hỏi khi bảo vệ đồ án.
 *
 * ⚠️ KHÔNG BỊA THÔNG TIN DOANH NGHIỆP. Chân trang của STUDY4 (ảnh chủ dự án gửi) có tên
 * công ty, mã số thuế, giấy phép, hotline. MoodBite là ĐỒ ÁN TỐT NGHIỆP — không có công
 * ty, không có giấy phép kinh doanh, không có tổng đài. Chép cấu trúc đó rồi điền số
 * liệu giả là bịa dữ liệu, đúng thứ `CLAUDE.md` mục 0 cấm.
 */
import { Link } from 'react-router-dom';
import { ROUTES } from '@/shared/config';
import { useT } from '@/shared/i18n';

/**
 * Nguồn dữ liệu + giấy phép. Sửa ở đây khi thêm/bớt nguồn — và phải khớp với
 * `docs/data_sources.md`, đừng để hai nơi nói hai kiểu.
 */
const NGUON_DU_LIEU = [
  { ten: 'OpenStreetMap', giay_phep: 'ODbL 1.0', url: 'https://www.openstreetmap.org/copyright' },
  { ten: 'Overture Maps', giay_phep: 'CDLA-Permissive-2.0', url: 'https://overturemaps.org/' },
  { ten: 'Wikipedia · Wikimedia Commons', giay_phep: 'CC BY-SA', url: 'https://vi.wikipedia.org/' },
];

export function SiteFooter() {
  const t = useT();

  return (
    <footer className="site-footer">
      <div className="site-footer__grid">
        <div className="site-footer__cot site-footer__cot--gioi-thieu">
          <p className="site-footer__ten">MoodBite</p>
          <p className="site-footer__mo-ta">{t('footer.tagline')}</p>
          {/* Nói thẳng phạm vi. Người dùng ở Đà Nẵng mở lên rồi mới phát hiện không có
              quán nào thì đó là lỗi của ta, không phải của họ. */}
          <p className="site-footer__pham-vi">{t('footer.scope')}</p>
        </div>

        <nav className="site-footer__cot" aria-label={t('footer.navLabel')}>
          <p className="site-footer__tieu-de">{t('footer.exploreTitle')}</p>
          <Link to={ROUTES.home}>{t('nav.suggest')}</Link>
          <Link to={ROUTES.search}>{t('nav.search')}</Link>
          <Link to={ROUTES.account}>{t('footer.account')}</Link>
        </nav>

        <div className="site-footer__cot">
          <p className="site-footer__tieu-de">{t('footer.dataTitle')}</p>
          {NGUON_DU_LIEU.map((nguon) => (
            <a
              key={nguon.ten}
              href={nguon.url}
              target="_blank"
              // `noopener` bắt buộc khi mở tab mới: thiếu nó thì trang đích đọc được
              // `window.opener` và điều hướng tab của ta đi chỗ khác.
              rel="noopener noreferrer"
            >
              {nguon.ten} <span className="site-footer__giay-phep">({nguon.giay_phep})</span>
            </a>
          ))}
        </div>

        <div className="site-footer__cot">
          <p className="site-footer__tieu-de">{t('footer.honestTitle')}</p>
          {/* Nhắc lại đúng điều `CLAUDE.md` mục 4 quy tắc 4 bắt buộc: món là SUY LUẬN từ
              tên quán, ta CHƯA BAO GIỜ đọc thực đơn thật. Nói ở đây một lần cho cả app. */}
          <p className="site-footer__ghi-chu">{t('footer.dishDisclaimer')}</p>
          <p className="site-footer__ghi-chu">{t('footer.academic')}</p>
        </div>
      </div>

      <p className="site-footer__ban-quyen">{t('footer.copyright')}</p>
    </footer>
  );
}
