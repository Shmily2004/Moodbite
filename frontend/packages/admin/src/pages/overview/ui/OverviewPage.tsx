/**
 * TRANG TỔNG QUAN của khu quản trị — màn đầu tiên sau khi đăng nhập.
 *
 * Dựng theo `frontend/design/Dashboard admin.png` (chủ dự án gửi 2026-08-26):
 *
 *   Xin chào, Admin!                                  [cập nhật lúc] [⟳]
 *   [Tổng quán] [Tổng món] [Món có quán] [Món chưa có quán] [Cần xử lý → Xem chi tiết]
 *   ┌ Tình trạng dữ liệu ┐ ┌ Cần xử lý ┐ ┌ Hoạt động gần đây ┐
 *   ┌ Nguồn dữ liệu (vành khuyên) ┐ ┌ Hệ thống gợi ý ┐
 *
 * CẬP NHẬT 2026-09-16:
 *   - "Thống kê theo nguồn" vẽ bằng BIỂU ĐỒ VÀNH KHUYÊN SVG (giữ nguyên số + chú thích).
 *   - Khối "Hệ thống gợi ý" NAY CÓ THẬT, đếm từ nhật ký tương tác
 *     (`GET /admin/interactions/stats`): tổng lượt, tỷ lệ tín hiệu tích cực, số phiên /
 *     tài khoản, theo loại hành động, sparkline 7 ngày.
 *   - Các link "Xem chi tiết →" của bản thiết kế, CHỈ những link có trang thật để tới.
 *
 * ⚠️ VẪN CỐ TÌNH KHÔNG DỰNG — vì không có dữ liệu thật:
 *   1. "↗ +1.248 so với tuần trước" trên ô số: màn Tổng quan không đọc ảnh chụp theo ngày
 *      (xu hướng có ở trang "Chất lượng dữ liệu").
 *   2. "Tỷ lệ click (CTR) 8.7%": CTR = lượt bấm / lượt HIỂN THỊ, mà dự án KHÔNG ghi lượt
 *      hiển thị (impression) — không có mẫu số thì mọi con số CTR đều là bịa.
 *   3. "Lượt gợi ý hôm nay 1.306": lượt tìm kiếm không được ghi lại.
 *   4. Chuông thông báo: không có nguồn thông báo nào.
 *
 * Vẽ ra bằng số minh hoạ sẽ là bịa dữ liệu ngay trên màn hình dùng để KIỂM TRA dữ liệu —
 * CLAUDE.md mục 0 và mục 4.
 */
import { Link } from 'react-router-dom';
import { useOverview } from '@admin/features/view-overview';
import { ROUTES } from '@admin/shared/config';
import type { AdminOverviewData, DoPhuTruong, ViecCanXuLy } from '@admin/shared/api';
import { phanTramVN, soVN } from '@admin/shared/lib';
import { IconTron, type MauIconTron, type TenIcon } from '@admin/shared/ui';
import { DongCanXuLy, HoatDongGanDay } from './CanXuLyHoatDong';
import { HeThongGoiY, NguonDuLieu } from './NguonVaGoiY';

// Các khối con được tách sang file anh em ngày 2026-10-06 (file cũ vượt ~300 dòng):
// `NguonVaGoiY.tsx` (nguồn dữ liệu + hệ thống gợi ý), `CanXuLyHoatDong.tsx`.

export function OverviewPage() {
  const { data, loading, error, reload } = useOverview();

  return (
    <div className="tong-quan">
      {/* PHẦN ĐẦU LUÔN HIỆN, kể cả khi tải lỗi — backend tắt thì người quản trị vẫn biết
          mình đang ở màn nào và có nút thử lại. */}
      <header className="tong-quan__dau">
        <div>
          <h2 className="tong-quan__chao">Xin chào, Admin!</h2>
          <p className="muted">Đây là trung tâm vận hành dữ liệu của MoodBite.</p>
        </div>
        <div className="tong-quan__cap-nhat">
          {data && (
            <span className="muted">
              Số liệu tính lúc {new Date(data.generated_at).toLocaleString('vi-VN')}
            </span>
          )}
          <button className="ghost" onClick={reload} disabled={loading}>
            {loading ? 'Đang tính…' : '⟳ Tải lại'}
          </button>
        </div>
      </header>

      {/* Lỗi: báo và GIỮ NGUYÊN bảng cũ nếu còn. */}
      {error && (
        <p className={data ? 'notice notice--warn' : 'panel panel--error'}>{error}</p>
      )}

      {loading && !data && (
        <p className="panel muted" aria-busy="true">
          Đang tính số liệu…
        </p>
      )}

      {data && <NoiDung data={data} />}
    </div>
  );
}

/** Toàn bộ phần phụ thuộc dữ liệu. Tách ra để phần đầu trang không dính `data` nữa. */
function NoiDung({ data }: { data: AdminOverviewData }) {
  return (
    <>
      <ul className="the-so">
        <TheSo icon="quan-an" mau="xanh" nhan="Tổng số quán" so={data.restaurants_total} />
        <TheSo icon="mon-an" mau="cam" nhan="Tổng số món" so={data.dishes_total} />
        <TheSo
          icon="dau-tich"
          mau="luc"
          nhan="Món có quán tại Hà Nội"
          so={data.dishes_with_restaurants}
          phu={`${phanTramVN(data.dishes_with_restaurants, data.dishes_total)} tổng số món`}
        />
        <TheSo
          icon="dau-hoi"
          mau="tim"
          nhan="Món chưa có quán"
          so={data.dishes_without_restaurants}
          phu={`${phanTramVN(data.dishes_without_restaurants, data.dishes_total)} tổng số món`}
        />
        {/* Cùng nền trắng như bốn thẻ kia (bản thiết kế); lời mời hành động nằm ở chữ
            "Xem chi tiết" màu cam, không cần nhuộm vàng cả thẻ. */}
        <li className="the-so__o the-so__o--co-icon">
          <IconTron ten="can-xu-ly" mau="cam" />
          <div className="the-so__than">
            <span className="the-so__nhan">Cần xử lý</span>
            <span className="the-so__gia-tri">{soVN(data.needs_attention_total)}</span>
            <Link className="the-so__lien-ket" to={ROUTES.issues}>
              Xem chi tiết →
            </Link>
          </div>
        </li>
      </ul>
      {/* Nói rõ thứ CHƯA có ngay trên màn hình: im lặng thì người quản trị tưởng số không
          đổi so với tuần trước. */}
      <p className="muted small">
        Màn này không so sánh với tuần trước. Xu hướng theo ngày nằm ở{' '}
        <Link className="linkish" to={ROUTES.quality}>
          Chất lượng dữ liệu
        </Link>
        .
      </p>

      <div className="tong-quan__luoi">
        <section className="panel">
          <h3 className="panel__tieu-de">Tình trạng dữ liệu</h3>
          <ul className="do-phu">
            {data.data_quality.map((x: DoPhuTruong) => (
              <li key={x.key} className="do-phu__dong">
                <div className="do-phu__chu">
                  <span className="do-phu__nhan">{x.label}</span>
                  <span className="muted do-phu__mo-ta">{x.description}</span>
                </div>
                <div className="do-phu__thanh">
                  <div
                    className={`do-phu__day do-phu__day--${x.level}`}
                    style={{ width: `${x.percent}%` }}
                  />
                </div>
                {/* Số tuyệt đối DƯỚI phần trăm: "26,1%" một mình không cho biết là
                    13.812 hay 13 quán. Xếp chồng thay vì thêm cột để nhãn đủ chỗ. */}
                <span className="do-phu__cot-so">
                  <span className="do-phu__so">{x.percent}%</span>
                  <span className="muted do-phu__tuyet-doi">
                    {soVN(x.covered)}/{soVN(x.total)}
                  </span>
                </span>
              </li>
            ))}
          </ul>
          <p className="panel__chan">
            <Link className="linkish" to={ROUTES.quality}>
              Xem chi tiết báo cáo chất lượng dữ liệu →
            </Link>
          </p>
        </section>

        <section className="panel">
          <div className="bang__dau">
            <h3 className="panel__tieu-de">Cần xử lý</h3>
            <Link className="linkish" to={ROUTES.issues}>
              Xem tất cả →
            </Link>
          </div>
          <ul className="can-xu-ly">
            {data.needs_attention.map((v: ViecCanXuLy) => (
              <DongCanXuLy key={v.key} viec={v} />
            ))}
          </ul>
        </section>

        <HoatDongGanDay />
      </div>

      <div className="tong-quan__luoi tong-quan__luoi--hai">
        <NguonDuLieu data={data} />
        <HeThongGoiY data={data} />
      </div>
    </>
  );
}

function TheSo({
  nhan,
  so,
  phu,
  icon,
  mau,
}: {
  nhan: string;
  so: number;
  phu?: string;
  icon: TenIcon;
  mau: MauIconTron;
}) {
  return (
    <li className="the-so__o the-so__o--co-icon">
      <IconTron ten={icon} mau={mau} />
      <div className="the-so__than">
        <span className="the-so__nhan">{nhan}</span>
        <span className="the-so__gia-tri">{soVN(so)}</span>
        {phu && <span className="muted the-so__phu">{phu}</span>}
      </div>
    </li>
  );
}
