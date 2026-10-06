// Tách từ QualityPage.tsx ngày 2026-10-06 vì file vượt ~300 dòng (CLAUDE.md mục 6).
// Cột phải của trang: "Tình trạng dữ liệu", "Theo nguồn dữ liệu quán", "Xu hướng dữ liệu".
import { NHAN_NGUON_QUAN, nhanTheoMa } from '@/shared/config';
import type {
  AdminDataQualityData,
  AnhChupChatLuong,
  DoPhuTruong,
  ThongKeNguon,
} from '@/shared/api';
import { soVN } from './soVN';

/** Số nhóm nguồn hiện thành thanh; phần còn lại gộp — tránh bảng dài vì nguồn lặt vặt. */
const SO_NGUON_HIEN = 4;

/**
 * Vòng tròn "Tình trạng dữ liệu".
 *
 * Vẽ bằng `conic-gradient` thuần CSS, KHÔNG kéo thư viện biểu đồ: cả trang chỉ có đúng
 * một vòng tròn và một đường gấp khúc, thêm ~50KB JavaScript cho hai hình đó là không
 * đáng — và app quản trị vốn đã có ràng buộc "không thêm phụ thuộc nếu chưa cần".
 */
export function TinhTrangDuLieu({ data }: { data: AdminDataQualityData }) {
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

export function TheoNguon({ nguon, tong }: { nguon: ThongKeNguon[]; tong: number }) {
  return (
    <section className="panel">
      <h3 className="panel__tieu-de">Theo nguồn dữ liệu quán</h3>
      <ul className="nguon">
        {nguon.slice(0, SO_NGUON_HIEN).map((n) => (
          <li key={n.source} className="nguon__dong">
            <span className="nguon__ten">{nhanTheoMa(NHAN_NGUON_QUAN, n.source)}</span>
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
export function XuHuong({ diem, coLichSu }: { diem: AnhChupChatLuong[]; coLichSu: boolean }) {
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
