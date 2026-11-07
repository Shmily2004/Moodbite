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
import { useActivity } from '@admin/features/view-activity';
import { useDataQuality } from '@admin/features/view-data-quality';
import { ROUTES } from '@admin/shared/config';
import { Icon } from '@admin/shared/ui';
import type { AdminDataQualityData } from '@admin/shared/api';
import { soVN } from './soVN';
import { TheSo, TheSoCoMoc } from './TheSoChatLuong';
import { TinhTrangDuLieu, TheoNguon, XuHuong } from './TinhTrangXuHuong';
import { CanXuLyNgay, VanDeKhac } from './VanDeCanXuLy';

// Các khối con được tách sang file anh em ngày 2026-10-06 (file cũ vượt ~300 dòng):
// `VanDeCanXuLy.tsx` (cột trái), `TinhTrangXuHuong.tsx` (cột phải), `TheSoChatLuong.tsx`.

/** Số dòng nhật ký hiện ở cuối trang. */
const SO_NHAT_KY = 3;

export function QualityPage() {
  const { data, loading, error, reload } = useDataQuality();

  return (
    <div className="chat-luong">
      {/* PHẦN ĐẦU LUÔN HIỆN, kể cả khi tải lỗi — nếu không, backend tắt là cả trang
          trắng và người quản trị không còn nút nào để thử lại ngoài F5. */}
      <header className="tong-quan__dau">
        <div>
          <h2 className="tong-quan__chao tieu-de-icon tieu-de-icon--trang">
            <Icon ten="chat-luong" /> Chất lượng dữ liệu
          </h2>
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
        <TheSoCoMoc icon="quan-an" mau="xanh" nhan="Tổng số quán" thayDoi={data.restaurants_total} />
        <TheSoCoMoc icon="mon-an" mau="cam" nhan="Tổng số món" thayDoi={data.dishes_total} />
        <TheSo
          icon="ghim"
          mau="luc"
          nhan="Quán tại Hà Nội"
          so={data.restaurants_in_hanoi}
          phu={`${data.restaurants_in_hanoi_percent}% tổng số quán`}
        />
        <TheSo
          icon="can-xu-ly"
          mau="cam"
          nhan="Vấn đề nghiêm trọng"
          so={data.critical}
          nhanManh={data.critical > 0}
        />
        <TheSo
          icon="thong-tin"
          mau="tim"
          nhan="Vấn đề cần kiểm tra"
          so={data.to_review}
          nhanManh={data.to_review > 0}
        />
      </ul>

      <div className="chat-luong__luoi">
        <div className="chat-luong__cot">
          <CanXuLyNgay ban_ghi={data.needs_attention_now} nhom={data.needs_attention} />
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
