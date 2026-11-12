/**
 * Khối "Quán bị khách báo đóng cửa" trên trang Cần xử lý (thêm 2026-10-06).
 *
 * VIEW thuần: dữ liệu và thao tác đến từ `useClosureReports`. Không tự suy `is_hidden`.
 * Theo biểu đồ UC21: mỗi quán có hai lựa chọn — ẩn quán, hoặc gỡ lượt báo.
 */
import { useClosureReports } from '../model/useClosureReports';

export function ClosureReportsPanel() {
  const { items, loading, error, dangGo, anQuan, goBaoCao } = useClosureReports();

  return (
    <section className="panel bao-dong-cua" aria-labelledby="bao-dong-cua-tieu-de">
      <h3 id="bao-dong-cua-tieu-de" className="panel__title">
        Quán bị khách báo đóng cửa
      </h3>
      <p className="muted">
        Lượt báo của khách KHÔNG tự ẩn quán. Kiểm tra từng quán: nếu thật sự đã đóng cửa thì
        "Ẩn quán"; nếu không thì "Gỡ lượt báo" để xoá các lượt báo của quán đó.
      </p>

      {error && <p className="notice notice--warn">{error}</p>}
      {loading && items.length === 0 && (
        <p className="muted" aria-busy="true">
          Đang tải…
        </p>
      )}
      {!loading && !error && items.length === 0 && (
        <p className="muted">Chưa có quán nào bị khách báo đóng cửa.</p>
      )}

      {items.length > 0 && (
        <table className="bang">
          <thead>
            <tr>
              <th scope="col">Quán</th>
              <th scope="col">Số người báo</th>
              <th scope="col">Trạng thái</th>
              <th scope="col">Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {items.map((q) => (
              <tr key={q.restaurant_id}>
                {/* Quán có thể đã bị xoá khỏi dữ liệu mà lượt báo vẫn còn -> tên null. */}
                <td>{q.name ?? <span className="muted">{q.restaurant_id}</span>}</td>
                <td className="tnum">{q.report_count}</td>
                <td>
                  {q.is_hidden ? (
                    <span className="nhan nhan--loi">Đang bị ẩn</span>
                  ) : (
                    <span className="nhan nhan--canh-bao">Chờ xử lý</span>
                  )}
                </td>
                <td>
                  {!q.is_hidden && (
                    <button
                      type="button"
                      disabled={dangGo === q.restaurant_id}
                      onClick={() => void anQuan(q.restaurant_id)}
                      aria-label={`Ẩn quán ${q.name ?? q.restaurant_id} vì đã đóng cửa`}
                    >
                      Ẩn quán
                    </button>
                  )}{' '}
                  <button
                    type="button"
                    className="ghost"
                    disabled={dangGo === q.restaurant_id}
                    onClick={() => void goBaoCao(q.restaurant_id)}
                    aria-label={`Gỡ lượt báo đóng cửa của ${q.name ?? q.restaurant_id}`}
                  >
                    {dangGo === q.restaurant_id ? 'Đang xử lý…' : 'Gỡ lượt báo'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
