/** Trang 404 của app quản trị. */
import { Link } from 'react-router-dom';
import { ROUTES } from '@/shared/config';

export function NotFoundPage() {
  return (
    <div className="page">
      <h2>Không có trang này</h2>
      <p className="muted">Đường dẫn bạn mở không tồn tại trong trang quản trị.</p>
      <p>
        <Link to={ROUTES.restaurants}>← Về danh sách quán</Link>
      </p>
    </div>
  );
}
