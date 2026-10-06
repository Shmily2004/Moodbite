/**
 * TRANG LỖI CỦA ROUTE (`errorElement`) — thêm 2026-10-06.
 *
 * VÌ SAO: trang nặng được tải lười (`routes.tsx` → `taiSau`). Sau một lần deploy, file JS
 * cũ biến mất; tab đang mở bấm sang trang đó là `import()` thất bại. Không có
 * `errorElement` thì React Router hiện màn hình mặc định TIẾNG ANH "Unexpected
 * Application Error!" — người dùng không biết phải làm gì.
 *
 * Nút "Tải lại trang" là cách khắc phục đúng cho cả hai nguyên nhân hay gặp (file JS đã
 * đổi tên sau deploy, mạng chập chờn). Link về trang chủ là `<a>` thường, KHÔNG phải
 * `<Link>`: tải lại cả trang thì mới lấy được bản JS mới.
 */
import { useEffect } from 'react';
import { useRouteError } from 'react-router-dom';
import { useT } from '@/shared/i18n';

export function RouteError() {
  const loi = useRouteError();
  const t = useT();

  useEffect(() => {
    // Ghi lại cho người phát triển; người dùng chỉ thấy câu dễ hiểu bên dưới.
    console.error('Lỗi khi dựng route:', loi);
  }, [loi]);

  return (
    <div className="plain" role="alert">
      <h2>{t('routeErr.title')}</h2>
      <p className="muted">{t('routeErr.hint')}</p>
      <p>
        <button type="button" className="btn btn--primary" onClick={() => window.location.reload()}>
          {t('routeErr.reload')}
        </button>{' '}
        <a href="/">{t('routeErr.home')}</a>
      </p>
    </div>
  );
}
