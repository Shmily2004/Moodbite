/**
 * Tầng `app` — khởi tạo ứng dụng, bố cục chung, provider.
 * Chưa cần router vì hiện chỉ có một trang.
 */
import { SearchPage } from '@/pages/search';
import './styles.css';

export function App() {
  return (
    <div className="app">
      <header className="app__header">
        <h1>MoodBite</h1>
        <p className="muted">Gợi ý quán ăn theo nhu cầu, vị trí và thời điểm của bạn.</p>
      </header>

      <main>
        <SearchPage />
      </main>

      <footer className="app__footer muted">
        Khoảng cách theo đường chim bay. Món ăn là suy luận từ loại hình quán, chưa phải
        thực đơn thật. Dữ liệu bản đồ &copy;{' '}
        <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors.
      </footer>
    </div>
  );
}
