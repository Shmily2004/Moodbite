// Tách từ OverviewPage.tsx ngày 2026-10-06 vì file vượt ~300 dòng (CLAUDE.md mục 6).
// Hai hộp danh sách của lưới giữa: dòng "Cần xử lý" + "Hoạt động gần đây".
import { Link } from 'react-router-dom';
import { useActivity } from '@admin/features/view-activity';
import { DUONG_DAN_CAN_XU_LY, ROUTES } from '@admin/shared/config';
import type { ViecCanXuLy } from '@admin/shared/api';
import { ngayGioVN, soVN } from '@admin/shared/lib';

/**
 * Một dòng trong hộp "Cần xử lý".
 *
 * Bấm được -> `<Link>` sang danh sách ĐÃ LỌC SẴN. Chưa có đường dẫn -> `<li>` thường,
 * KHÔNG phải link chết.
 */
export function DongCanXuLy({ viec }: { viec: ViecCanXuLy }) {
  const duongDan = DUONG_DAN_CAN_XU_LY[viec.key];
  const lop =
    viec.severity === 'thong_tin'
      ? 'can-xu-ly__dong can-xu-ly__dong--tin'
      : 'can-xu-ly__dong';

  const noiDung = (
    <>
      <div>
        <p className="can-xu-ly__nhan">{viec.label}</p>
        <p className="muted can-xu-ly__mo-ta">{viec.description}</p>
      </div>
      <span className="can-xu-ly__so">
        {soVN(viec.count)}
        {duongDan && <span className="can-xu-ly__mui-ten" aria-hidden="true">›</span>}
      </span>
    </>
  );

  if (!duongDan) {
    return <li className={lop}>{noiDung}</li>;
  }
  return (
    <li>
      <Link className={`${lop} can-xu-ly__link`} to={duongDan}>
        {noiDung}
      </Link>
    </li>
  );
}

/**
 * "Hoạt động gần đây" — dữ liệu thật từ nhật ký hoạt động.
 *
 * Gọi `useActivity` riêng thay vì nhét vào `/admin/overview`: nhật ký đổi mỗi lần admin
 * thao tác, còn số liệu tổng quan được đệm 5 phút.
 */
export function HoatDongGanDay() {
  const { entries, available, loading } = useActivity();
  const SO_HIEN = 5;

  return (
    <section className="panel">
      <div className="bang__dau">
        <h3 className="panel__tieu-de">Hoạt động gần đây</h3>
        <Link className="linkish" to={ROUTES.activity}>
          Xem tất cả →
        </Link>
      </div>

      {loading && <p className="muted">Đang tải…</p>}
      {!loading && !available && (
        <p className="notice notice--warn">
          Không mở được kho nhật ký — đây <strong>không phải</strong> là "chưa có hoạt
          động nào".
        </p>
      )}
      {!loading && available && entries.length === 0 && (
        <p className="muted">Chưa có thao tác nào được ghi lại.</p>
      )}

      {entries.length > 0 && (
        <ul className="nhat-ky">
          {entries.slice(0, SO_HIEN).map((e, i) => (
            <li key={`${e.created_at}-${i}`} className="nhat-ky__dong">
              <div className="nhat-ky__chinh">
                <p className="nhat-ky__hanh-dong">{e.action_label}</p>
                <p className="muted nhat-ky__tom-tat">{e.summary}</p>
              </div>
              <span className="muted nhat-ky__gio">{ngayGioVN(e.created_at)}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
