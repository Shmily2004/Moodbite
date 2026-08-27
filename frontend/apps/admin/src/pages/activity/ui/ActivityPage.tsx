/**
 * TRANG NHẬT KÝ HOẠT ĐỘNG — ai đã ẩn/sửa/thêm quán, lúc nào.
 *
 * Trước 2026-08-26 khu quản trị KHÔNG ghi lại gì cả: một quán biến mất khỏi kết quả tìm
 * kiếm và không có cách nào truy ra ai đã ẩn nó. Nay mỗi thao tác sửa dữ liệu đều để lại
 * một dòng — xem `domain/entities/audit_log.py`.
 *
 * ⚠️ RỖNG KHÔNG PHẢI LÚC NÀO CŨNG LÀ "CHƯA AI LÀM GÌ". Cờ `available` do backend trả
 * phân biệt hai chuyện: nhật ký trống thật, và kho nhật ký không mở được. Gộp lại thì
 * người quản trị yên tâm rằng không có hoạt động nào trong khi thực ra nhật ký đang hỏng
 * — đúng kiểu im lặng nguy hiểm mà CLAUDE.md mục 4 cấm.
 */
import { useActivity } from '@/features/view-activity';
import type { AuditEntry } from '@/shared/api';

/** Giữ đồng bộ với `AuditAction` ở `domain/entities/audit_log.py`. */
const LOC: { khoa: string | null; nhan: string }[] = [
  { khoa: null, nhan: 'Tất cả' },
  { khoa: 'create_restaurant', nhan: 'Thêm quán' },
  { khoa: 'update_restaurant', nhan: 'Sửa quán' },
  { khoa: 'hide_restaurant', nhan: 'Ẩn quán' },
  { khoa: 'restore_restaurant', nhan: 'Khôi phục' },
];

export function ActivityPage() {
  const { entries, available, action, setAction, loading, error, reload } = useActivity();

  return (
    <section className="panel">
      <div className="bang__dau">
        <h2 className="panel__tieu-de">Nhật ký hoạt động</h2>
        <button className="ghost" onClick={reload} disabled={loading}>
          {loading ? 'Đang tải…' : '⟳ Tải lại'}
        </button>
      </div>
      <p className="muted">
        Mọi thao tác thêm / sửa / ẩn / khôi phục quán đều được ghi lại. Chỉ ghi thêm,
        không sửa và không xoá được từng dòng.
      </p>

      <div className="chip-hang" role="group" aria-label="Lọc theo hành động">
        {LOC.map((l) => (
          <button
            key={l.nhan}
            type="button"
            className={action === l.khoa ? 'chip chip--dang' : 'chip'}
            aria-pressed={action === l.khoa}
            onClick={() => setAction(l.khoa)}
          >
            {l.nhan}
          </button>
        ))}
      </div>

      {error && <p className="notice notice--warn">{error}</p>}

      {/* Hai trạng thái rỗng KHÁC NHAU — xem docstring đầu file. */}
      {!available && (
        <p className="notice notice--warn">
          Không mở được kho nhật ký, nên đây <strong>không phải</strong> là "chưa có hoạt
          động nào". Kiểm tra quyền ghi ở đường dẫn <code>MOODBITE_USERS_DB</code>.
        </p>
      )}

      {available && !loading && entries.length === 0 && (
        <p className="muted">
          {action
            ? 'Chưa có thao tác nào thuộc nhóm này.'
            : 'Chưa có thao tác nào được ghi lại.'}
        </p>
      )}

      {entries.length > 0 && (
        <ul className="nhat-ky">
          {entries.map((e, i) => (
            <DongNhatKy key={`${e.created_at}-${i}`} muc={e} />
          ))}
        </ul>
      )}
    </section>
  );
}

function DongNhatKy({ muc }: { muc: AuditEntry }) {
  return (
    <li className="nhat-ky__dong">
      <div className="nhat-ky__chinh">
        <p className="nhat-ky__hanh-dong">{muc.action_label}</p>
        <p className="muted nhat-ky__tom-tat">{muc.summary}</p>
        <p className="muted nhat-ky__ma">
          {muc.target_type}: <code>{muc.target_id}</code>
        </p>
      </div>
      <div className="nhat-ky__ben">
        <span className="nhan nhan--tin">{muc.actor}</span>
        <span className="muted nhat-ky__gio">
          {muc.created_at ? new Date(muc.created_at).toLocaleString('vi-VN') : '—'}
        </span>
      </div>
    </li>
  );
}
