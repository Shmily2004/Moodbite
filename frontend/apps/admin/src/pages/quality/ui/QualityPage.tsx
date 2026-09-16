/**
 * TRANG "CHẤT LƯỢNG DỮ LIỆU" của khu quản trị.
 *
 * Dựng theo `frontend/design/quality data admin.png` (chủ dự án gửi 2026-09-08):
 *
 *   Chất lượng dữ liệu                       [trạng thái] [cập nhật lần cuối] [⟳]
 *   [Tổng quán] [Tổng món] [Quán tại HN] [Vấn đề nghiêm trọng] [Vấn đề cần kiểm tra]
 *   ┌ Cần xử lý ngay ────────────┐ ┌ Tình trạng dữ liệu (vòng tròn) ┐
 *   │ (bản ghi cụ thể, có tên)   │ ├ Theo nguồn dữ liệu quán ───────┤
 *   ├ Các vấn đề khác ───────────┤ └ Xu hướng dữ liệu ──────────────┘
 *   └ Hoạt động gần đây ─────────┘
 *
 * ⚠️ HAI CON SỐ TRONG BẢN THIẾT KẾ CỐ TÌNH KHÔNG DỰNG, vì không có nguồn dữ liệu:
 *   1. "Dữ liệu an toàn" như một nhãn tự đánh giá — dự án không có tiêu chí nào định
 *      nghĩa được thế nào là "an toàn". Thay bằng câu nói thẳng còn bao nhiêu việc gấp.
 *   2. Ảnh đại diện quán trong khối "Cần xử lý ngay" — chỉ 21,5% quán có ảnh, nên phần
 *      lớn dòng sẽ là ô xám. Vẫn hiện ảnh KHI CÓ, không có thì bỏ trống chứ không chèn
 *      ảnh mẫu (chèn ảnh mẫu = nói dối rằng đã biết quán trông thế nào).
 *
 * NGƯỢC LẠI, hai thứ trước đây KHÔNG dựng được thì NAY CÓ THẬT: "so với tháng trước" và
 * biểu đồ xu hướng. Chúng dựa trên bảng `quality_snapshot` ghi mỗi ngày một dòng. Ngày
 * đầu chạy sẽ chỉ có một điểm và `delta` là `null` — trang phải nói "chưa đủ dữ liệu để
 * so sánh", TUYỆT ĐỐI không hiện mũi tên hay số 0 (CLAUDE.md mục 4).
 */
import { Link } from 'react-router-dom';
import { useActivity } from '@/features/view-activity';
import { useDataQuality } from '@/features/view-data-quality';
import { DUONG_DAN_CAN_XU_LY, ROUTES } from '@/shared/config';
import type {
  AdminDataQualityData,
  AnhChupChatLuong,
  BanGhiVanDe,
  DoPhuTruong,
  ThayDoi,
  ThongKeNguon,
  VanDeNhom,
} from '@/shared/api';

/** Số nhóm nguồn hiện thành thanh; phần còn lại gộp — tránh bảng dài vì nguồn lặt vặt. */
const SO_NGUON_HIEN = 4;

/** Số dòng nhật ký hiện ở cuối trang. */
const SO_NHAT_KY = 3;

function soVN(n: number): string {
  return n.toLocaleString('vi-VN');
}

export function QualityPage() {
  const { data, loading, error, reload } = useDataQuality();

  return (
    <div className="chat-luong">
      {/* PHẦN ĐẦU LUÔN HIỆN, kể cả khi tải lỗi — nếu không, backend tắt là cả trang
          trắng và người quản trị không còn nút nào để thử lại ngoài F5. */}
      <header className="tong-quan__dau">
        <div>
          <h2 className="tong-quan__chao">Chất lượng dữ liệu</h2>
          <p className="muted">
            Giám sát và xử lý các vấn đề về dữ liệu để đảm bảo thông tin luôn chính xác,
            đầy đủ và cập nhật.
          </p>
        </div>
        <div className="tong-quan__cap-nhat">
          {data && (
            <span className="muted">
              Cập nhật lần cuối {new Date(data.generated_at).toLocaleString('vi-VN')}
            </span>
          )}
          <button className="ghost" onClick={reload} disabled={loading}>
            {loading ? 'Đang tính…' : '⟳ Làm mới'}
          </button>
        </div>
      </header>

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

function NoiDung({ data }: { data: AdminDataQualityData }) {
  const conGap = data.critical + data.important;

  return (
    <>
      {/* Thay cho nhãn "Dữ liệu an toàn" của bản thiết kế: một câu ĐO ĐƯỢC thay vì một
          lời tự khen không có tiêu chí. */}
      <p className={conGap > 0 ? 'notice notice--warn' : 'notice'}>
        {conGap > 0 ? (
          <>
            Còn <strong>{soVN(conGap)}</strong> bản ghi ở mức nghiêm trọng hoặc quan
            trọng. <Link to={ROUTES.issues}>Xem danh sách cần xử lý →</Link>
          </>
        ) : (
          <>Không còn bản ghi nào ở mức nghiêm trọng hoặc quan trọng.</>
        )}
      </p>

      <ul className="the-so">
        <TheSoCoMoc nhan="Tổng số quán" thayDoi={data.restaurants_total} />
        <TheSoCoMoc nhan="Tổng số món" thayDoi={data.dishes_total} />
        <TheSo
          nhan="Quán tại Hà Nội"
          so={data.restaurants_in_hanoi}
          phu={`${data.restaurants_in_hanoi_percent}% tổng số quán`}
        />
        <TheSo nhan="Vấn đề nghiêm trọng" so={data.critical} nhanManh={data.critical > 0} />
        <TheSo nhan="Vấn đề cần kiểm tra" so={data.to_review} />
      </ul>

      <div className="chat-luong__luoi">
        <div className="chat-luong__cot">
          <CanXuLyNgay ban_ghi={data.needs_attention_now} />
          <VanDeKhac nhom={data.needs_attention} />
        </div>

        <div className="chat-luong__cot">
          <TinhTrangDuLieu data={data} />
          <TheoNguon nguon={data.by_source} tong={data.restaurants_total.current} />
          <XuHuong diem={data.trend} coLichSu={data.history_available} />
        </div>
      </div>

      <HoatDongGanDay />
    </>
  );
}

/**
 * Khối "Cần xử lý ngay" — vài bản ghi CỤ THỂ, có tên tuổi, ưu tiên nhóm gấp nhất.
 *
 * Khác khối "Các vấn đề khác" ở chỗ đây là bản ghi thật để bấm vào mà sửa, còn kia là
 * con số tổng. Bản thiết kế có cả hai vì chúng trả lời hai câu khác nhau: "sửa cái gì
 * ngay bây giờ" và "tổng thể đang hỏng những gì".
 */
function CanXuLyNgay({ ban_ghi }: { ban_ghi: BanGhiVanDe[] }) {
  return (
    <section className="panel">
      <div className="bang__dau">
        <h3 className="panel__tieu-de">Cần xử lý ngay</h3>
        <Link className="linkish" to={ROUTES.issues}>
          Xem tất cả →
        </Link>
      </div>

      {ban_ghi.length === 0 ? (
        <p className="muted">Không có bản ghi nào đang chờ xử lý.</p>
      ) : (
        <ul className="viec-ngay">
          {ban_ghi.map((b) => (
            <li key={`${b.key}-${b.id}`} className="viec-ngay__dong">
              {/* Ảnh CHỈ hiện khi có. Chèn ảnh mẫu vào chỗ trống là nói dối rằng đã
                  biết quán/món trông thế nào. */}
              {b.image_url ? (
                <img className="viec-ngay__anh" src={b.image_url} alt="" loading="lazy" />
              ) : (
                <span className="viec-ngay__anh viec-ngay__anh--trong" aria-hidden="true" />
              )}
              <div className="viec-ngay__chu">
                <p className="viec-ngay__ten">{b.name}</p>
                {b.description && <p className="muted small">{b.description}</p>}
              </div>
              <Link className="ghost viec-ngay__nut" to={`${ROUTES.issues}?nhom=${b.key}`}>
                Xem chi tiết
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/** Khối "Các vấn đề khác" — con số tổng của những nhóm KHÔNG gấp. */
function VanDeKhac({ nhom }: { nhom: VanDeNhom[] }) {
  const khac = nhom.filter((v) => v.priority === 'can_kiem_tra');

  return (
    <section className="panel">
      <h3 className="panel__tieu-de">Các vấn đề khác</h3>
      <ul className="van-de-khac">
        {khac.map((v) => {
          const duongDan = DUONG_DAN_CAN_XU_LY[v.key];
          return (
            <li key={v.key} className="van-de-khac__o">
              <span className="van-de-khac__nhan">{v.label}</span>
              <span className="van-de-khac__so">{soVN(v.count)}</span>
              {/* Chưa có đường dẫn thì KHÔNG dựng link chết: dẫn tới một danh sách không
                  lọc đúng thứ vừa hứa còn tệ hơn là không bấm được. */}
              {duongDan ? (
                <Link className="linkish small" to={duongDan}>
                  Xem danh sách →
                </Link>
              ) : (
                <Link className="linkish small" to={`${ROUTES.issues}?nhom=${v.key}`}>
                  Xem danh sách →
                </Link>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

/**
 * Vòng tròn "Tình trạng dữ liệu".
 *
 * Vẽ bằng `conic-gradient` thuần CSS, KHÔNG kéo thư viện biểu đồ: cả trang chỉ có đúng
 * một vòng tròn và một đường gấp khúc, thêm ~50KB JavaScript cho hai hình đó là không
 * đáng — và app quản trị vốn đã có ràng buộc "không thêm phụ thuộc nếu chưa cần".
 */
function TinhTrangDuLieu({ data }: { data: AdminDataQualityData }) {
  const day = data.completeness_percent;
  const thieu = Math.round((100 - day) * 10) / 10;
  const coBan = data.data_quality.find((x: DoPhuTruong) => x.key === 'co_ban');
  const tong = coBan?.total ?? data.restaurants_total.current;
  const soDay = coBan?.covered ?? 0;

  return (
    <section className="panel">
      <h3 className="panel__tieu-de">Tình trạng dữ liệu</h3>
      <div className="vong-tron">
        <div
          className="vong-tron__hinh"
          style={{
            background: `conic-gradient(var(--open) 0 ${day}%, var(--warn) ${day}% 100%)`,
          }}
          role="img"
          aria-label={`${day}% quán có đủ thông tin cơ bản`}
        >
          <div className="vong-tron__ruot">
            <strong className="vong-tron__so">{day}%</strong>
            <span className="muted small">Hoàn thiện</span>
          </div>
        </div>
        <ul className="vong-tron__chu-thich">
          <li>
            <span className="cham cham--tot" aria-hidden="true" />
            Có đầy đủ thông tin <b>{day}%</b> <span className="muted">({soVN(soDay)})</span>
          </li>
          <li>
            <span className="cham cham--thieu" aria-hidden="true" />
            Chưa hoàn thiện <b>{thieu}%</b>{' '}
            <span className="muted">({soVN(Math.max(tong - soDay, 0))})</span>
          </li>
        </ul>
      </div>
      <p className="muted panel__ghi-chu">
        "Đầy đủ" = có cả địa chỉ, khu vực và loại hình. Đánh giá và giá <em>không</em> tính
        vào đây vì chúng đến từ nguồn làm giàu, độ phủ thấp là chuyện đã biết.
      </p>
    </section>
  );
}

function TheoNguon({ nguon, tong }: { nguon: ThongKeNguon[]; tong: number }) {
  return (
    <section className="panel">
      <h3 className="panel__tieu-de">Theo nguồn dữ liệu quán</h3>
      <ul className="nguon">
        {nguon.slice(0, SO_NGUON_HIEN).map((n) => (
          <li key={n.source} className="nguon__dong">
            <span className="nguon__ten">{n.source}</span>
            <div className="do-phu__thanh">
              <div
                className="do-phu__day do-phu__day--tot"
                style={{ width: `${n.percent}%` }}
              />
            </div>
            <span className="nguon__so">
              {n.percent}% <span className="muted">({soVN(n.count)})</span>
            </span>
          </li>
        ))}
      </ul>
      <p className="muted panel__ghi-chu">Tổng {soVN(tong)} quán.</p>
    </section>
  );
}

/**
 * Biểu đồ "Xu hướng dữ liệu" — 7 ngày gần nhất.
 *
 * MỘT ĐIỂM THÌ KHÔNG VẼ ĐƯỜNG, và phải nói rõ vì sao. Một đường phẳng dựng từ một điểm
 * duy nhất trông y như "đã theo dõi cả tuần và không có gì đổi" — sai hoàn toàn.
 */
function XuHuong({ diem, coLichSu }: { diem: AnhChupChatLuong[]; coLichSu: boolean }) {
  return (
    <section className="panel">
      <h3 className="panel__tieu-de">Xu hướng dữ liệu</h3>

      {!coLichSu && (
        <p className="notice notice--warn">
          Không mở được kho lịch sử — đây <strong>không phải</strong> là "không có vấn đề
          gì".
        </p>
      )}

      {coLichSu && diem.length < 2 ? (
        <p className="muted">
          Mới ghi được {diem.length} ngày. Biểu đồ cần ít nhất 2 ngày để vẽ được xu hướng
          — mỗi lần mở trang này ghi thêm một điểm cho hôm nay, nên vài ngày nữa sẽ có.
        </p>
      ) : (
        coLichSu && <DuongXuHuong diem={diem} />
      )}
    </section>
  );
}

/**
 * Đường gấp khúc bằng SVG thuần.
 *
 * Thang đo lấy theo GIÁ TRỊ LỚN NHẤT trong chuỗi, không cố định — số vấn đề dao động từ
 * vài đơn vị tới hàng nghìn tuỳ nhóm, thang cứng sẽ làm mọi đường dính đáy.
 */
function DuongXuHuong({ diem }: { diem: AnhChupChatLuong[] }) {
  const R = 240;
  const C = 90;
  const dem = Math.max(
    1,
    ...diem.map((d) => Math.max(d.critical, d.important)),
  );

  const toaDo = (lay: (d: AnhChupChatLuong) => number) =>
    diem
      .map((d, i) => {
        const x = diem.length === 1 ? R / 2 : (i / (diem.length - 1)) * R;
        const y = C - (lay(d) / dem) * C;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');

  return (
    <>
      <svg
        className="xu-huong"
        viewBox={`0 0 ${R} ${C}`}
        preserveAspectRatio="none"
        role="img"
        aria-label={`Xu hướng vấn đề trong ${diem.length} ngày gần nhất`}
      >
        <polyline className="xu-huong__nghiem-trong" points={toaDo((d) => d.critical)} />
        <polyline className="xu-huong__quan-trong" points={toaDo((d) => d.important)} />
      </svg>
      <ul className="xu-huong__chu-thich">
        <li>
          <span className="cham cham--loi" aria-hidden="true" /> Vấn đề nghiêm trọng
        </li>
        <li>
          <span className="cham cham--thieu" aria-hidden="true" /> Vấn đề quan trọng
        </li>
      </ul>
      <p className="muted panel__ghi-chu">
        {new Date(diem[0].date).toLocaleDateString('vi-VN')} –{' '}
        {new Date(diem[diem.length - 1].date).toLocaleDateString('vi-VN')} ·{' '}
        {diem.length} ngày có số liệu. Ngày không mở trang thì không có điểm — đường nối
        thẳng qua, <em>không</em> bù bằng 0.
      </p>
    </>
  );
}

/** Dùng lại đúng khối của trang Tổng quan: cùng một nhật ký, không có gì khác nhau. */
function HoatDongGanDay() {
  const { entries, available, loading } = useActivity();

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
          {entries.slice(0, SO_NHAT_KY).map((e, i) => (
            <li key={`${e.created_at}-${i}`} className="nhat-ky__dong">
              <div className="nhat-ky__chinh">
                <p className="nhat-ky__hanh-dong">{e.action_label}</p>
                <p className="muted nhat-ky__tom-tat">{e.summary}</p>
              </div>
              <span className="muted nhat-ky__gio">
                {e.created_at ? new Date(e.created_at).toLocaleString('vi-VN') : '—'}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/**
 * Thẻ số CÓ so sánh với mốc quá khứ.
 *
 * `delta === null` -> nói "chưa đủ dữ liệu để so sánh". KHÔNG hiện mũi tên, KHÔNG hiện
 * "+0": cả hai đều nghe như đã so xong và kết luận là không đổi.
 */
function TheSoCoMoc({ nhan, thayDoi }: { nhan: string; thayDoi: ThayDoi }) {
  const d = thayDoi.delta;

  return (
    <li className="the-so__o">
      <span className="the-so__nhan">{nhan}</span>
      <span className="the-so__gia-tri">{soVN(thayDoi.current)}</span>
      {d === null || d === undefined ? (
        <span className="muted the-so__phu">Chưa đủ dữ liệu để so sánh</span>
      ) : (
        <span
          className={
            d > 0 ? 'the-so__phu the-so__phu--tang' : 'muted the-so__phu'
          }
        >
          {d > 0 ? '↗ +' : d < 0 ? '↘ ' : ''}
          {d === 0 ? 'Không đổi' : soVN(Math.abs(d))}
          {d !== 0 && ' so với '}
          {d !== 0 &&
            thayDoi.baseline_date &&
            new Date(thayDoi.baseline_date).toLocaleDateString('vi-VN')}
        </span>
      )}
    </li>
  );
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
