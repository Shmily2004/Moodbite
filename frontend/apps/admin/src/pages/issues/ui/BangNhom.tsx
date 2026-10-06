/**
 * Bảng NHÓM vấn đề + danh sách bản ghi của nhóm đang mở (tách khỏi `IssuesPage.tsx`
 * 2026-10-06 khi file đó vượt ~300 dòng).
 */
import { useIssueDetail } from '@/features/manage-issues';
import type { BanGhiVanDe, VanDeNhom } from '@/shared/api';
import { NHAN_UU_TIEN_VAN_DE, nhanTheoMa } from '@/shared/config';
import { ngayGioVN } from '@/shared/lib';
import { NHAN_LOAI, soVN } from './hienThi';

export function BangNhom({
  nhom,
  nhomDangMo,
  onMo,
  onChanged,
}: {
  nhom: VanDeNhom[];
  nhomDangMo: string | null;
  onMo: (khoa: string | null) => void;
  /** Đánh dấu xong → trang tải lại bộ đếm (số lượng nhóm + năm thẻ số). */
  onChanged: () => void;
}) {
  if (nhom.length === 0) {
    return <p className="panel muted">Không có nhóm vấn đề nào khớp bộ lọc đã chọn.</p>;
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
              <th title="Lần gần nhất một bản ghi trong nhóm được đánh dấu xử lý">
                Xử lý gần nhất
              </th>
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
                    {nhanTheoMa(NHAN_UU_TIEN_VAN_DE, v.priority)}
                  </span>
                </td>
                <td className="tnum">{soVN(v.count)}</td>
                <td className="small muted">{ngayGioVN(v.last_resolved_at)}</td>
                <td>
                  {/* Nhóm 0 bản ghi vẫn hiện dòng (đó là câu trả lời "đã kiểm, không có
                      gì") nhưng KHÔNG mở được danh sách rỗng — bấm vào chỉ để thấy trống. */}
                  {v.count > 0 ? (
                    <button
                      type="button"
                      className="ghost"
                      onClick={() => onMo(nhomDangMo === v.key ? null : v.key)}
                    >
                      {nhomDangMo === v.key ? 'Đóng' : 'Xem danh sách ›'}
                    </button>
                  ) : (
                    // Ô trống trơn trông như nút bị lỗi không hiện; nói thẳng là không có gì.
                    <span className="muted small">Không có</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {nhomDangMo && <ChiTietNhom khoa={nhomDangMo} onChanged={onChanged} />}
    </section>
  );
}

/**
 * Danh sách BẢN GHI cụ thể của một nhóm.
 *
 * Dòng đã đánh dấu xử lý vẫn HIỆN, chỉ tô mờ — giấu đi thì người bấm nhầm không còn cách
 * nào tìm lại để gỡ.
 */
function ChiTietNhom({ khoa, onChanged }: { khoa: string; onChanged: () => void }) {
  const { data, loading, error, actionError, dangGui, danhDau } = useIssueDetail(
    khoa,
    onChanged,
  );

  if (loading && !data) {
    return <p className="muted" aria-busy="true">Đang tải danh sách…</p>;
  }
  if (error) {
    return <p className="notice notice--warn">{error}</p>;
  }
  if (!data) return null;

  return (
    <div className="chi-tiet-nhom">
      {/* Lỗi ĐÁNH DẤU hiện ngay trên danh sách — danh sách vẫn còn để làm tiếp. */}
      {actionError && (
        <p className="notice notice--warn" role="alert">
          {actionError}
        </p>
      )}
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
