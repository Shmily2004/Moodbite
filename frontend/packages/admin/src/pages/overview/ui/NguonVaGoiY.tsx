// Tách từ OverviewPage.tsx ngày 2026-10-06 vì file vượt ~300 dòng (CLAUDE.md mục 6).
// Hàng dưới của trang Tổng quan: "Thống kê theo nguồn dữ liệu" + "Hệ thống gợi ý".
import { Link } from 'react-router-dom';
import { useInteractionStats } from '@admin/features/view-overview';
import { NHAN_HANH_DONG_TUONG_TAC, NHAN_NGUON_QUAN, ROUTES, nhanTheoMa } from '@admin/shared/config';
import type { AdminInteractionStatsData, AdminOverviewData } from '@admin/shared/api';
import { ngayGioVN, phanTramVN, soVN } from '@admin/shared/lib';
import { Sparkline, VanhKhuyen } from '@admin/shared/ui';

/** Số nguồn vẽ thành phần riêng; phần còn lại gộp "Khác" — tránh vành khuyên vụn. */
const SO_NGUON_HIEN = 5;

/**
 * "Thống kê theo nguồn dữ liệu" — vành khuyên + chú thích có SỐ.
 * Nguồn nhỏ gộp thành "Khác" để vành không vụn; số của "Khác" vẫn cộng đúng.
 */
export function NguonDuLieu({ data }: { data: AdminOverviewData }) {
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
export function HeThongGoiY({ data }: { data: AdminOverviewData }) {
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
