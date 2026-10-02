/**
 * VIEW: toàn bộ trường của MỘT món — tab "Thông tin chi tiết" ở trang chi tiết món.
 *
 * Trước 2026-09-16 phần này nằm trong ô trượt `DishDetailPanel` bên cạnh bảng món. Nay
 * chi tiết món là một ROUTE THẬT (`/mon-an/:dishId`), nên nội dung được giữ nguyên và
 * chuyển sang đây; ô trượt đã bỏ.
 *
 * ⚠️ CHỈ ĐỌC. Không có nút Sửa vì `dish_catalog.json` là file do
 * `scripts/build_dish_catalog.py` SINH RA — sửa qua đây sẽ bị lần chạy sau ghi đè.
 */
import type { AdminDishDetail } from '@/shared/api';
import {
  NHAN_BUA_AN,
  NHAN_CACH_CHE_BIEN,
  NHAN_NGUON_MON,
  NHAN_NHIET_DO_MON,
  nhanTheoMa,
} from '@/shared/config';
import { ngayGioVN } from '@/shared/lib';

export function DishInfo({ data }: { data: AdminDishDetail }) {
  // `match_keywords`/`meal_times` có `default_factory` ở backend nên kiểu sinh ra là
  // optional. Chuẩn hoá một lần ở đây thay vì rải `?? []` khắp phần dựng.
  const tuKhoa = data.match_keywords ?? [];
  const bua = data.meal_times ?? [];

  return (
    <div className="chi-tiet__than">
      <h4 className="chi-tiet__nhan">Giới thiệu</h4>
      {data.description ? (
        <p className="chi-tiet__mo-ta">{data.description}</p>
      ) : (
        <p className="muted">Chưa tra được giới thiệu cho món này.</p>
      )}

      {/* Từ khoá đối chiếu là thứ QUYẾT ĐỊNH món này ra quán nào. Với admin đang đi tìm
          "vì sao món X không ra quán nào", đây là thông tin quan trọng nhất. */}
      <h4 className="chi-tiet__nhan">Từ khoá đối chiếu tên quán</h4>
      {tuKhoa.length > 0 ? (
        <ul className="chip-hang">
          {tuKhoa.map((k) => (
            <li key={k} className="chip">
              {k}
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted">
          Không có từ khoá riêng — hệ thống đối chiếu bằng chính tên món.
        </p>
      )}

      <h4 className="chi-tiet__nhan">Thuộc tính</h4>
      <dl className="cau-hinh">
        <Muc nhan="Mã món" giaTri={data.dish_id} />
        <Muc nhan="Tên món" giaTri={data.name} />
        <Muc nhan="Ẩm thực" giaTri={data.cuisine ?? '—'} />
        <Muc nhan="Loại" giaTri={data.is_category ? 'Danh mục (gồm nhiều món)' : 'Món cụ thể'} />
        {/* Mã thô ("hot", "nuoc") đổi sang chữ người đọc; mã lạ thì hiện nguyên mã. */}
        <Muc nhan="Nhiệt độ" giaTri={nhanTheoMa(NHAN_NHIET_DO_MON, data.temperature)} />
        <Muc nhan="Cách chế biến" giaTri={nhanTheoMa(NHAN_CACH_CHE_BIEN, data.cooking_method)} />
        <Muc
          nhan="Độ cay"
          // `null` là CHƯA BIẾT, khác hẳn `0` là KHÔNG CAY (CLAUDE.md mục 4).
          giaTri={data.spice_level == null ? 'chưa biết' : String(data.spice_level)}
        />
        <Muc
          nhan="Bữa phù hợp"
          giaTri={bua.length ? bua.map((b) => nhanTheoMa(NHAN_BUA_AN, b)).join(', ') : '—'}
        />
        <Muc nhan="Nguồn mô tả" giaTri={nhanTheoMa(NHAN_NGUON_MON, data.source)} />
        <Muc nhan="Cập nhật" giaTri={ngayGioVN(data.last_updated)} />
      </dl>

      {data.source_url && (
        <p>
          <a className="linkish" href={data.source_url} target="_blank" rel="noreferrer">
            Xem nguồn gốc →
          </a>
        </p>
      )}
    </div>
  );
}

function Muc({ nhan, giaTri }: { nhan: string; giaTri: string }) {
  return (
    <div className="cau-hinh__muc">
      <dt>{nhan}</dt>
      <dd>{giaTri}</dd>
    </div>
  );
}
