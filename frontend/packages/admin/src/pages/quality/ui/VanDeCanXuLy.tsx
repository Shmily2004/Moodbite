// Tách từ QualityPage.tsx ngày 2026-10-06 vì file vượt ~300 dòng (CLAUDE.md mục 6).
// Cột trái của trang: "Cần xử lý ngay" + "Các vấn đề khác".
import { Link } from 'react-router-dom';
import { DUONG_DAN_CAN_XU_LY, NHAN_UU_TIEN_VAN_DE, ROUTES, nhanTheoMa } from '@admin/shared/config';
import { AnhThuNho, Icon } from '@admin/shared/ui';
import type { BanGhiVanDe, VanDeNhom } from '@admin/shared/api';
import { soVN } from './soVN';

/**
 * Khối "Cần xử lý ngay" — vài bản ghi CỤ THỂ, có tên tuổi, ưu tiên nhóm gấp nhất.
 *
 * Khác khối "Các vấn đề khác" ở chỗ đây là bản ghi thật để bấm vào mà sửa, còn kia là
 * con số tổng. Bản thiết kế có cả hai vì chúng trả lời hai câu khác nhau: "sửa cái gì
 * ngay bây giờ" và "tổng thể đang hỏng những gì".
 */
export function CanXuLyNgay({ ban_ghi, nhom }: { ban_ghi: BanGhiVanDe[]; nhom: VanDeNhom[] }) {
  // Bản ghi chỉ mang `key` của nhóm; tên vấn đề + mức ưu tiên tra từ danh sách nhóm mà
  // backend đã trả cùng lượt. Chỉ là TRA CỨU để hiển thị, không tự xếp loại lại.
  const theoKhoa = new Map(nhom.map((v) => [v.key, v]));

  return (
    <section className="panel">
      <div className="bang__dau">
        <h3 className="panel__tieu-de tieu-de-icon">
          <Icon ten="can-xu-ly" className="icon icon--canh-bao" /> Cần xử lý ngay
        </h3>
        <Link className="linkish" to={ROUTES.issues}>
          Xem tất cả →
        </Link>
      </div>

      {ban_ghi.length === 0 ? (
        <p className="muted">Không có bản ghi nào đang chờ xử lý.</p>
      ) : (
        <ul className="viec-ngay">
          {ban_ghi.map((b) => {
            const v = theoKhoa.get(b.key);
            return (
              <li key={`${b.key}-${b.id}`} className="viec-ngay__dong">
                {/* Ảnh CHỈ hiện khi có (và link còn sống). Chèn ảnh mẫu vào chỗ trống là
                    nói dối rằng đã biết quán/món trông thế nào. */}
                <AnhThuNho
                  src={b.image_url}
                  className="viec-ngay__anh"
                  classNameTrong="viec-ngay__anh--trong"
                />
                <div className="viec-ngay__chu">
                  {/* Không tra được nhóm (backend thêm nhóm mới) -> bỏ dòng tiêu đề, KHÔNG
                      hiện mã thô cho người quản trị. */}
                  {v && <p className="viec-ngay__loai">{v.label}</p>}
                  <p className="viec-ngay__ten">{b.name}</p>
                  {b.description && <p className="muted small">{b.description}</p>}
                </div>
                {v ? (
                  <span className={`pill pill--${v.priority}`}>
                    {nhanTheoMa(NHAN_UU_TIEN_VAN_DE, v.priority)}
                  </span>
                ) : (
                  <span />
                )}
                {/* KHÔNG có cột "x ngày trước" của bản thiết kế: backend không lưu thời
                    điểm phát hiện vấn đề, con số đó sẽ phải bịa. */}
                <Link
                  className="nut-chinh nut-nho viec-ngay__nut"
                  to={`${ROUTES.issues}?nhom=${b.key}`}
                >
                  Xem chi tiết
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

/** Khối "Các vấn đề khác" — con số tổng của những nhóm KHÔNG gấp. */
export function VanDeKhac({ nhom }: { nhom: VanDeNhom[] }) {
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
