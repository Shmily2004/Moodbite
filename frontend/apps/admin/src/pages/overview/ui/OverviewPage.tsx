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
import { useActivity } from '@/features/view-activity';
import { useInteractionStats, useOverview } from '@/features/view-overview';
import {
  DUONG_DAN_CAN_XU_LY,
  NHAN_HANH_DONG_TUONG_TAC,
  NHAN_NGUON_QUAN,
  ROUTES,
  nhanTheoMa,
} from '@/shared/config';
import type {
  AdminInteractionStatsData,
  AdminOverviewData,
  DoPhuTruong,
  ViecCanXuLy,
} from '@/shared/api';
import { ngayGioVN, phanTramVN, soVN } from '@/shared/lib';
import { IconTron, Sparkline, VanhKhuyen, type MauIconTron, type TenIcon } from '@/shared/ui';

/** Số nguồn vẽ thành phần riêng; phần còn lại gộp "Khác" — tránh vành khuyên vụn. */
const SO_NGUON_HIEN = 5;

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

/**
 * "Thống kê theo nguồn dữ liệu" — vành khuyên + chú thích có SỐ.
 * Nguồn nhỏ gộp thành "Khác" để vành không vụn; số của "Khác" vẫn cộng đúng.
 */
function NguonDuLieu({ data }: { data: AdminOverviewData }) {
  const dau = data.by_source.slice(0, SO_NGUON_HIEN);
  const conLai = data.by_source.slice(SO_NGUON_HIEN);
  const phan = [
    ...dau.map((n) => ({
      nhan: nhanTheoMa(NHAN_NGUON_QUAN, n.source),
      giaTri: n.count,
      phanTram: n.percent,
    })),
    ...(conLai.length
      ? [
          {
            nhan: 'Khác',
            giaTri: conLai.reduce((s, n) => s + n.count, 0),
            phanTram: Math.round(conLai.reduce((s, n) => s + n.percent, 0) * 10) / 10,
          },
        ]
      : []),
  ];

  return (
    <section className="panel">
      <h3 className="panel__tieu-de">Thống kê theo nguồn dữ liệu</h3>
      <div className="nguon-vanh">
        <VanhKhuyen
          phan={phan}
          chuGiua={soVN(data.restaurants_total)}
          chuPhu="Tổng quán"
          nhan={`Tỷ lệ quán theo nguồn: ${phan
            .map((p) => `${p.nhan} ${p.phanTram}%`)
            .join(', ')}`}
        />
        <ul className="nguon-vanh__chu-thich">
          {phan.map((p, i) => (
            <li key={p.nhan}>
              <span className={`cham mau-nen-bieu-do-${(i % 6) + 1}`} />
              <span className="nguon-vanh__ten">{p.nhan}</span>
              <span className="tnum">
                {p.phanTram.toLocaleString('vi-VN')}%{' '}
                <span className="muted">({soVN(p.giaTri)})</span>
              </span>
            </li>
          ))}
        </ul>
      </div>
      <p className="muted panel__ghi-chu">
        Tổng {soVN(data.restaurants_total)} quán
        {data.restaurants_hidden > 0 && `, trong đó ${soVN(data.restaurants_hidden)} đã ẩn`}.
      </p>
      <p className="panel__chan">
        <Link className="linkish" to={ROUTES.quality}>
          Xem báo cáo dữ liệu đầy đủ →
        </Link>
      </p>
    </section>
  );
}

/**
 * "Hệ thống gợi ý" — đếm THẬT từ nhật ký tương tác.
 *
 * ⚠️ KHÔNG có ô CTR, và đây là chủ đích: CTR cần số lượt HIỂN THỊ làm mẫu số, dự án không
 * ghi lượt hiển thị. Ô "Độ phủ món" lấy từ `/admin/overview` (đã có sẵn trên trang).
 */
function HeThongGoiY({ data }: { data: AdminOverviewData }) {
  const { data: tk, loading, error } = useInteractionStats();

  return (
    <section className="panel">
      <h3 className="panel__tieu-de">Hệ thống gợi ý</h3>
      {loading && !tk && <p className="muted">Đang tải…</p>}
      {error && <p className="notice notice--warn">{error}</p>}
      {tk && !tk.available && (
        <p className="notice notice--warn">
          Không đọc được nhật ký tương tác — đây <strong>không phải</strong> là "chưa có ai
          dùng".
        </p>
      )}
      {tk && tk.available && tk.total === 0 && (
        <p className="muted">
          Chưa có lượt tương tác nào được ghi. Khối này sẽ có số khi người dùng bắt đầu xem,
          lưu hoặc chỉ đường tới quán.
        </p>
      )}
      {tk && tk.available && tk.total > 0 && <NoiDungGoiY tk={tk} data={data} />}
      <p className="muted panel__ghi-chu">
        Chưa có "Tỷ lệ click (CTR)" và "Lượt gợi ý hôm nay": hệ thống chưa ghi lượt quán được
        hiển thị và lượt tìm kiếm, nên không có mẫu số để tính.
      </p>
      <p className="panel__chan">
        <Link className="linkish" to={ROUTES.recommendation}>
          Xem chi tiết hệ thống gợi ý →
        </Link>
      </p>
    </section>
  );
}

function NoiDungGoiY({
  tk,
  data,
}: {
  tk: AdminInteractionStatsData;
  data: AdminOverviewData;
}) {
  const ngay = tk.last_7_days;
  const tongTuan = ngay.reduce((s, d) => s + d.count, 0);
  return (
    <>
      <ul className="o-goi-y">
        <li className="o-goi-y__o">
          <span className="the-so__nhan">Lượt tương tác</span>
          <span className="the-so__gia-tri">{soVN(tk.total)}</span>
          <span className="muted small">{soVN(tongTuan)} lượt trong 7 ngày</span>
          <Sparkline
            giaTri={ngay.map((d) => d.count)}
            nhan={`Lượt tương tác 7 ngày: ${ngay
              .map((d) => `${ngayGioVN(d.date)} ${d.count}`)
              .join(', ')}`}
          />
        </li>
        <li className="o-goi-y__o">
          <span className="the-so__nhan">Tín hiệu tích cực</span>
          <span className="the-so__gia-tri">
            {tk.positive_rate == null ? '—' : `${tk.positive_rate.toLocaleString('vi-VN')}%`}
          </span>
          <span className="muted small">
            {tk.positive_rate == null
              ? 'chưa có bản ghi mang nhãn'
              : 'lưu, chỉ đường, thích, xem lâu'}
          </span>
        </li>
        <li className="o-goi-y__o">
          <span className="the-so__nhan">Phiên / tài khoản</span>
          <span className="the-so__gia-tri">
            {soVN(tk.sessions)} <span className="muted small">/ {soVN(tk.users)}</span>
          </span>
          <span className="muted small">phiên trình duyệt / tài khoản đăng nhập</span>
        </li>
        <li className="o-goi-y__o">
          <span className="the-so__nhan">Độ phủ món</span>
          <span className="the-so__gia-tri">{soVN(data.dishes_with_restaurants)}</span>
          <span className="muted small">
            {phanTramVN(data.dishes_with_restaurants, data.dishes_total)} tổng món
          </span>
        </li>
      </ul>
      {/* Cần tiêu đề: không có nó, dòng "Xem chi tiết 3" trông như một link hỏng. */}
      {tk.by_action.length > 0 && (
        <p className="muted small goi-y-hanh-dong__tieu-de">Lượt tương tác theo loại hành động</p>
      )}
      <ul className="goi-y-hanh-dong" aria-label="Lượt tương tác theo loại hành động">
        {tk.by_action.map((a) => (
          <li key={a.action_type}>
            <span>{nhanTheoMa(NHAN_HANH_DONG_TUONG_TAC, a.action_type)}</span>
            <span className="tnum">{soVN(a.count)}</span>
          </li>
        ))}
      </ul>
    </>
  );
}

/**
 * Một dòng trong hộp "Cần xử lý".
 *
 * Bấm được -> `<Link>` sang danh sách ĐÃ LỌC SẴN. Chưa có đường dẫn -> `<li>` thường,
 * KHÔNG phải link chết.
 */
function DongCanXuLy({ viec }: { viec: ViecCanXuLy }) {
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
function HoatDongGanDay() {
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
