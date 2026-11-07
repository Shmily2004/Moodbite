/**
 * TRANG LỖI CỦA ROUTE (`errorElement`) — thêm 2026-10-06.
 *
 * Không có nó thì một lỗi khi dựng trang (hoặc tải file JS thất bại sau deploy) hiện màn
 * hình mặc định tiếng Anh "Unexpected Application Error!" của React Router.
 * Link về tổng quan là `<a>` thường để tải lại cả trang (lấy bản JS mới).
 */
import { useEffect } from 'react';
import { useRouteError } from 'react-router-dom';
import { ROUTES } from '@admin/shared/config';

export function RouteError() {
  const loi = useRouteError();

  useEffect(() => {
    console.error('Lỗi khi dựng route:', loi);
  }, [loi]);

  return (
    <div className="page" role="alert">
      <h2>Không mở được trang này</h2>
      <p className="muted">
        Có thể trang quản trị vừa được cập nhật hoặc mạng bị gián đoạn. Tải lại trang thường
        sẽ khắc phục được.
      </p>
      <p>
        <button type="button" className="btn" onClick={() => window.location.reload()}>
          Tải lại trang
        </button>{' '}
        <a href={ROUTES.overview}>Về tổng quan</a>
      </p>
    </div>
  );
}
