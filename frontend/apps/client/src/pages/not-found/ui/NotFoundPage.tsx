/** Trang 404. Nói rõ đường dẫn sai và đưa người dùng về chỗ dùng được. */
import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <div className="plain">
      <h2>Không có trang này</h2>
      <p className="muted">
        Đường dẫn bạn mở không tồn tại. Có thể link đã cũ hoặc gõ nhầm.
      </p>
      <p>
        <Link to="/">← Quay lại trang tìm quán</Link>
      </p>
    </div>
  );
}
