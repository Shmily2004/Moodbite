import type { AdminResolvedIssue } from '@/shared/api';
import { ngayGioVN } from '@/shared/lib';

/** Tab "Đã xử lý": bản ghi đã được đánh dấu, mới nhất đứng đầu. */
export function BangDaXuLy({
  dong,
  loading,
  error,
}: {
  dong: AdminResolvedIssue[] | null;
  loading: boolean;
  error: string | null;
}) {
  if (loading && !dong) return <p className="panel muted">Đang tải…</p>;
  if (error) return <p className="notice notice--warn">{error}</p>;
  if (!dong) return null;
  if (dong.length === 0) {
    return <p className="panel muted">Chưa có bản ghi nào được đánh dấu đã xử lý.</p>;
  }
  return (
    <section className="panel">
      <div className="table-scroll">
        <table className="bang-van-de">
          <thead>
            <tr>
              <th>Bản ghi</th>
              <th>Nhóm vấn đề</th>
              <th>Người xử lý</th>
              <th>Thời điểm</th>
            </tr>
          </thead>
          <tbody>
            {dong.map((d) => (
              <tr key={`${d.key}-${d.target_id}`} className="row">
                <td>
                  {/* Không tra được tên (quán đã ẩn, món đổi mã) thì hiện MÃ, không bịa tên. */}
                  <b>{d.name ?? d.target_id}</b>
                  {d.note && <p className="muted small">{d.note}</p>}
                </td>
                <td>{d.group_label ?? d.key}</td>
                <td>{d.resolved_by}</td>
                <td className="small">{ngayGioVN(d.resolved_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
