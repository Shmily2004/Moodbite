/**
 * TRANG TỔNG QUAN của khu quản trị — màn đầu tiên sau khi đăng nhập.
 *
 * Dựng theo `frontend/design/Dashboard admin.png` (chủ dự án gửi 2026-08-26):
 *
 *   Xin chào, Admin!                                  [cập nhật lúc] [⟳]
 *   [Tổng quán] [Tổng món] [Món có quán] [Món chưa có quán] [Cần xử lý]
 *   ┌ Tình trạng dữ liệu ┐ ┌ Cần xử lý ┐ ┌ Nguồn dữ liệu ┐
 *
 * ⚠️ BỐN KHỐI TRONG BẢN THIẾT KẾ CỐ TÌNH KHÔNG DỰNG — vì không có dữ liệu thật:
 *
 *   1. "↗ +1.248 so với tuần trước" trên mỗi ô số
 *   2. "Hoạt động gần đây" (ẩn quán / sửa quán / thêm quán, kèm giờ)
 *   3. "Hệ thống gợi ý": Lượt gợi ý hôm nay · CTR 8.7% · các đường sparkline
 *   4. Chuông thông báo với số 12
 *
 * Lý do cho từng cái:
 *   (1) và (3) cần ẢNH CHỤP DỮ LIỆU THEO NGÀY — dự án không lưu, nên không có cách nào
 *       biết "so với tuần trước". CTR cần lượt click; `interactions.jsonl` có 3 bản ghi.
 *   (2) cần NHẬT KÝ HOẠT ĐỘNG — chưa có bảng nào ghi lại việc admin ẩn/sửa/thêm quán.
 *   (4) không có nguồn thông báo nào. Số "cần xử lý" đã nằm ngay trên đầu trang rồi.
 *
 * Vẽ ra bằng số minh hoạ sẽ là bịa dữ liệu ngay trên màn hình dùng để KIỂM TRA dữ liệu —
 * CLAUDE.md mục 0 và mục 4. Ba mục còn thiếu đã ghi vào `PROJECT_CHECKLIST.md`.
 */
import { useOverview } from '@/features/view-overview';
import type {
  AdminOverviewData,
  DoPhuTruong,
  ThongKeNguon,
  ViecCanXuLy,
} from '@/shared/api';

/** Số nhóm nguồn hiện thành thanh; phần còn lại gộp — tránh bảng dài vì nguồn lặt vặt. */
const SO_NGUON_HIEN = 5;

function soVN(n: number): string {
  return n.toLocaleString('vi-VN');
}

export function OverviewPage() {
  const { data, loading, error, reload } = useOverview();

  return (
    <div className="tong-quan">
      {/* PHẦN ĐẦU LUÔN HIỆN, kể cả khi tải lỗi.
          Bản đầu trả về sớm khi chưa có `data`, nên backend tắt là cả trang trắng — người
          quản trị không còn biết mình đang ở màn nào và cũng không có nút thử lại nào
          ngoài F5. */}
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

      {/* Lỗi: báo và GIỮ NGUYÊN bảng cũ nếu còn. Xoá sạch màn hình vì một lần tải lại
          hỏng thì người quản trị mất luôn số liệu vừa đọc. */}
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
        <TheSo nhan="Tổng số quán" so={data.restaurants_total} />
        <TheSo nhan="Tổng số món" so={data.dishes_total} />
        <TheSo
          nhan="Món có quán tại Hà Nội"
          so={data.dishes_with_restaurants}
          phu={`${phanTram(data.dishes_with_restaurants, data.dishes_total)} tổng số món`}
        />
        <TheSo
          nhan="Món chưa có quán"
          so={data.dishes_without_restaurants}
          phu={`${phanTram(data.dishes_without_restaurants, data.dishes_total)} tổng số món`}
        />
        <TheSo nhan="Cần xử lý" so={data.needs_attention_total} nhanManh />
      </ul>

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
                <span className="do-phu__so">{x.percent}%</span>
                {/* Số tuyệt đối để cạnh phần trăm: "26,1%" một mình không cho biết là
                    13.812 hay 13 quán, mà hai con số đó dẫn tới hai quyết định khác nhau. */}
                <span className="muted do-phu__tuyet-doi">
                  {soVN(x.covered)}/{soVN(x.total)}
                </span>
              </li>
            ))}
          </ul>
        </section>

        <section className="panel">
          <h3 className="panel__tieu-de">Cần xử lý</h3>
          <ul className="can-xu-ly">
            {data.needs_attention.map((v: ViecCanXuLy) => (
              <li
                key={v.key}
                className={
                  v.severity === 'thong_tin'
                    ? 'can-xu-ly__dong can-xu-ly__dong--tin'
                    : 'can-xu-ly__dong'
                }
              >
                <div>
                  <p className="can-xu-ly__nhan">{v.label}</p>
                  <p className="muted can-xu-ly__mo-ta">{v.description}</p>
                </div>
                <span className="can-xu-ly__so">{soVN(v.count)}</span>
              </li>
            ))}
          </ul>
          {/* Nói thẳng vì sao chưa bấm vào được, thay vì làm nút chết. */}
          <p className="muted panel__ghi-chu">
            Chưa bấm vào được — màn danh sách lọc theo từng nhóm chưa dựng.
          </p>
        </section>

        <section className="panel">
          <h3 className="panel__tieu-de">Thống kê theo nguồn dữ liệu</h3>
          <ul className="nguon">
            {data.by_source.slice(0, SO_NGUON_HIEN).map((n: ThongKeNguon) => (
              <li key={n.source} className="nguon__dong">
                <span className="nguon__ten">{n.source}</span>
                <div className="do-phu__thanh">
                  <div className="do-phu__day do-phu__day--tot" style={{ width: `${n.percent}%` }} />
                </div>
                <span className="nguon__so">
                  {n.percent}% <span className="muted">({soVN(n.count)})</span>
                </span>
              </li>
            ))}
          </ul>
          <p className="muted panel__ghi-chu">
            Tổng {soVN(data.restaurants_total)} quán
            {data.restaurants_hidden > 0 && `, trong đó ${soVN(data.restaurants_hidden)} đã ẩn`}.
          </p>
        </section>
      </div>

      {/* Nói rõ thứ CHƯA có, ngay trên màn hình. Người quản trị phải biết mình đang không
          nhìn thấy gì — im lặng sẽ khiến họ tưởng "không có hoạt động nào". */}
      <section className="panel panel--chua-co">
        <h3 className="panel__tieu-de">Chưa có dữ liệu để hiện</h3>
        <ul className="chua-co">
          <li>
            <strong>Hoạt động gần đây</strong> — chưa có bảng nhật ký, nên việc admin
            ẩn/sửa/thêm quán hiện không được ghi lại ở đâu cả.
          </li>
          <li>
            <strong>So sánh với tuần trước</strong> — dự án không lưu ảnh chụp dữ liệu
            theo ngày, nên không tính được xu hướng.
          </li>
          <li>
            <strong>Hệ thống gợi ý (lượt gợi ý, tỷ lệ click)</strong> — mới có{' '}
            {soVN(data.interactions_total)} lượt tương tác được ghi. Cần người dùng thật
            trước đã.
          </li>
        </ul>
      </section>
    </>
  );
}

function phanTram(phan: number, tong: number): string {
  if (tong <= 0) return '0%';
  return `${Math.round((phan / tong) * 1000) / 10}%`;
}

function TheSo({
  nhan,
  so,
  phu,
  nhanManh = false,
}: {
  nhan: string;
  so: number;
  phu?: string;
  nhanManh?: boolean;
}) {
  return (
    <li className={nhanManh ? 'the-so__o the-so__o--nhan' : 'the-so__o'}>
      <span className="the-so__nhan">{nhan}</span>
      <span className="the-so__gia-tri">{soVN(so)}</span>
      {phu && <span className="muted the-so__phu">{phu}</span>}
    </li>
  );
}
