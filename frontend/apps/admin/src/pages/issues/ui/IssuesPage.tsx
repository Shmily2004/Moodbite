/**
 * TRANG "CẦN XỬ LÝ" của khu quản trị — inbox vấn đề dữ liệu.
 *
 * Dựng theo `frontend/design/needs to be handled admin.png` (chủ dự án gửi 2026-09-08):
 *
 *   Cần xử lý  (N)                                              [⟳ Làm mới]
 *   [Nghiêm trọng] [Quan trọng] [Cần kiểm tra] [Đã xử lý hôm nay] [Tổng số]
 *   Tab: Tất cả · Nghiêm trọng · Quan trọng · Cần kiểm tra · Đã xử lý
 *   Bảng: Vấn đề | Loại | Độ ưu tiên | Số lượng | Thao tác
 *   (bấm "Xem danh sách" -> mở các bản ghi cụ thể, đánh dấu xong được)
 *
 * ⚠️ HAI CHỖ KHÁC BẢN THIẾT KẾ, CÓ LÝ DO:
 *
 *  1. Cột "Cập nhật gần nhất" — bản thiết kế ghi giờ cụ thể cho từng NHÓM. Dự án không
 *     lưu thời điểm phát hiện vấn đề, nên con số đó sẽ phải bịa. Cột này bị bỏ; thay vào
 *     đó mỗi BẢN GHI cụ thể hiện ngày NGUỒN cập nhật (thứ đo được thật) khi mở chi tiết.
 *
 *  2. Phân trang "1 2 … 23" — bản thiết kế phân trang theo NHÓM, nhưng chỉ có 7 nhóm nên
 *     không cần trang thứ hai. Phần cần giới hạn là danh sách BẢN GHI bên trong một nhóm
 *     (nhóm lớn nhất có 8.920 bản ghi), và chỗ đó đã có trần 200 do server đặt.
 *
 * ⚠️ NĂM THẺ SỐ KHÔNG ĐỔI KHI BẤM TAB. Chúng luôn tính trên toàn bộ dữ liệu; nếu chúng
 * tụt theo tab thì bấm "Nghiêm trọng" sẽ trông như vừa xử lý xong mọi thứ khác.
 */
import { useSearchParams } from 'react-router-dom';
import { useIssueDetail, useIssues } from '@/features/manage-issues';
import type { BanGhiVanDe, UuTienVanDe, VanDeNhom } from '@/shared/api';

/** Nhãn tiếng Việt của mức ưu tiên. Khoá do backend đặt (`data_issues.py`). */
const NHAN_UU_TIEN: Record<UuTienVanDe, string> = {
  nghiem_trong: 'Nghiêm trọng',
  quan_trong: 'Quan trọng',
  can_kiem_tra: 'Cần kiểm tra',
};

/** Nhãn tiếng Việt của loại đối tượng. */
const NHAN_LOAI: Record<string, string> = {
  quan_an: 'Quán ăn',
  mon_an: 'Món ăn',
  du_lieu: 'Dữ liệu',
};

const TABS: Array<{ khoa: UuTienVanDe | null; nhan: string }> = [
  { khoa: null, nhan: 'Tất cả' },
  { khoa: 'nghiem_trong', nhan: 'Nghiêm trọng' },
  { khoa: 'quan_trong', nhan: 'Quan trọng' },
  { khoa: 'can_kiem_tra', nhan: 'Cần kiểm tra' },
];

function soVN(n: number): string {
  return n.toLocaleString('vi-VN');
}

export function IssuesPage() {
  const { data, loading, error, uuTien, chonUuTien, reload } = useIssues();
  // Nhóm đang mở chi tiết. Lấy từ query string để chia sẻ được link và F5 không mất —
  // đúng như trang `/recommend` của app client đã làm.
  const [thamSo, datThamSo] = useSearchParams();
  const nhomDangMo = thamSo.get('nhom');

  const moNhom = (khoa: string | null) => {
    const moi = new URLSearchParams(thamSo);
    if (khoa) moi.set('nhom', khoa);
    else moi.delete('nhom');
    datThamSo(moi);
  };

  return (
    <div className="can-xu-ly-trang">
      <header className="tong-quan__dau">
        <div>
          <h2 className="tong-quan__chao">
            Cần xử lý{' '}
            {data && <span className="huy-hieu-so">{soVN(data.critical)}</span>}
          </h2>
          <p className="muted">
            Các vấn đề cần kiểm tra và xử lý để đảm bảo chất lượng dữ liệu.
          </p>
        </div>
        <button className="ghost" onClick={reload} disabled={loading}>
          {loading ? 'Đang tải…' : '⟳ Làm mới'}
        </button>
      </header>

      {error && (
        <p className={data ? 'notice notice--warn' : 'panel panel--error'}>{error}</p>
      )}

      {loading && !data && (
        <p className="panel muted" aria-busy="true">
          Đang tính số liệu…
        </p>
      )}

      {data && (
        <>
          <ul className="the-so" aria-label="Tổng hợp vấn đề">
            <TheSo nhan="Nghiêm trọng" phu="Cần xử lý ngay" so={data.critical} nhanManh={data.critical > 0} />
            <TheSo nhan="Quan trọng" phu="Xử lý sớm" so={data.important} />
            <TheSo nhan="Cần kiểm tra" phu="Ưu tiên trung bình" so={data.to_review} />
            <TheSo nhan="Đã xử lý hôm nay" phu="Hoàn thành" so={data.resolved_today} />
            <TheSo nhan="Tổng số vấn đề" phu="Tất cả" so={data.total} />
          </ul>

          {!data.can_resolve && (
            <p className="notice notice--warn">
              Không mở được kho đánh dấu xử lý — nút "Đánh dấu đã xử lý" đang tắt. Vẫn xem
              được danh sách bình thường.
            </p>
          )}

          <nav className="tab-loc" aria-label="Lọc theo mức ưu tiên">
            {TABS.map((t) => (
              <button
                key={t.nhan}
                type="button"
                className={
                  uuTien === t.khoa ? 'tab-loc__nut tab-loc__nut--dang' : 'tab-loc__nut'
                }
                onClick={() => chonUuTien(t.khoa)}
              >
                {t.nhan}
                {t.khoa === null && ` (${soVN(data.total)})`}
                {t.khoa === 'nghiem_trong' && ` (${soVN(data.critical)})`}
                {t.khoa === 'quan_trong' && ` (${soVN(data.important)})`}
                {t.khoa === 'can_kiem_tra' && ` (${soVN(data.to_review)})`}
              </button>
            ))}
            <span className="muted small tab-loc__da-xong">
              Đã đánh dấu xử lý: {soVN(data.resolved_total)}
            </span>
          </nav>

          <BangNhom
            nhom={data.groups}
            nhomDangMo={nhomDangMo}
            onMo={moNhom}
          />
        </>
      )}
    </div>
  );
}

function BangNhom({
  nhom,
  nhomDangMo,
  onMo,
}: {
  nhom: VanDeNhom[];
  nhomDangMo: string | null;
  onMo: (khoa: string | null) => void;
}) {
  if (nhom.length === 0) {
    return <p className="panel muted">Không có nhóm vấn đề nào ở mức đã chọn.</p>;
  }

  return (
    <section className="panel">
      <div className="table-scroll">
        <table className="bang-van-de">
          <thead>
            <tr>
              <th>Vấn đề</th>
              <th>Loại</th>
              <th>Độ ưu tiên</th>
              <th className="tnum">Số lượng</th>
              <th>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {nhom.map((v) => (
              <tr key={v.key} className={v.count === 0 ? 'row row--rong' : 'row'}>
                <td>
                  <b>{v.label}</b>
                  <p className="muted small">{v.description}</p>
                </td>
                <td>
                  <span className="pill pill--off">
                    {NHAN_LOAI[v.target_type] ?? v.target_type}
                  </span>
                </td>
                <td>
                  <span className={`pill pill--${v.priority}`}>
                    {NHAN_UU_TIEN[v.priority as UuTienVanDe] ?? v.priority}
                  </span>
                </td>
                <td className="tnum">{soVN(v.count)}</td>
                <td>
                  {/* Nhóm 0 bản ghi vẫn hiện dòng (đó là câu trả lời "đã kiểm, không có
                      gì") nhưng KHÔNG mở được danh sách rỗng — bấm vào chỉ để thấy trống. */}
                  {v.count > 0 && (
                    <button
                      type="button"
                      className="ghost"
                      onClick={() => onMo(nhomDangMo === v.key ? null : v.key)}
                    >
                      {nhomDangMo === v.key ? 'Đóng' : 'Xem danh sách ›'}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {nhomDangMo && <ChiTietNhom khoa={nhomDangMo} />}
    </section>
  );
}

/**
 * Danh sách BẢN GHI cụ thể của một nhóm.
 *
 * Dòng đã đánh dấu xử lý vẫn HIỆN, chỉ tô mờ — giấu đi thì người bấm nhầm không còn cách
 * nào tìm lại để gỡ.
 */
function ChiTietNhom({ khoa }: { khoa: string }) {
  const { data, loading, error, dangGui, danhDau } = useIssueDetail(khoa);

  if (loading && !data) {
    return <p className="muted" aria-busy="true">Đang tải danh sách…</p>;
  }
  if (error) {
    return <p className="notice notice--warn">{error}</p>;
  }
  if (!data) return null;

  return (
    <div className="chi-tiet-nhom">
      <p className="muted small">
        Hiển thị {soVN(data.results.length)} trong {soVN(data.total)} bản ghi.
        {data.results.length < data.total &&
          ' Sửa bớt rồi mở lại để thấy phần còn lại.'}
      </p>

      {data.results.length === 0 ? (
        <p className="muted">Không còn bản ghi nào trong nhóm này.</p>
      ) : (
        <ul className="ban-ghi">
          {data.results.map((b: BanGhiVanDe) => (
            <li
              key={b.id}
              className={b.resolved_at ? 'ban-ghi__dong ban-ghi__dong--xong' : 'ban-ghi__dong'}
            >
              <div className="ban-ghi__chu">
                <p className="ban-ghi__ten">{b.name}</p>
                <p className="muted small">
                  {b.description || 'Chưa có thông tin khu vực'}
                  {/* Ngày NGUỒN cập nhật, KHÔNG phải ngày phát hiện lỗi. Thiếu thì im
                      lặng chứ không đoán (CLAUDE.md mục 4 quy tắc 1). */}
                  {b.source_updated_at &&
                    ` · nguồn cập nhật ${new Date(b.source_updated_at).toLocaleDateString('vi-VN')}`}
                </p>
                {b.resolved_at && (
                  <p className="muted small">
                    Đã đánh dấu xử lý bởi {b.resolved_by ?? 'admin'} lúc{' '}
                    {new Date(b.resolved_at).toLocaleString('vi-VN')}
                  </p>
                )}
              </div>
              <button
                type="button"
                className="ghost"
                disabled={dangGui === b.id}
                onClick={() => danhDau(b.id, !b.resolved_at)}
              >
                {dangGui === b.id
                  ? 'Đang lưu…'
                  : b.resolved_at
                    ? 'Gỡ đánh dấu'
                    : 'Đánh dấu đã xử lý'}
              </button>
            </li>
          ))}
        </ul>
      )}

      <p className="muted small">
        Đánh dấu xử lý <strong>không sửa dữ liệu</strong> — nó chỉ ghi lại rằng bạn đã xem
        và kết luận không phải làm gì thêm. Muốn sửa thật thì vào Quản lý quán / Quản lý món.
      </p>
    </div>
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
