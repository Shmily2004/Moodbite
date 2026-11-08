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
import { useState } from 'react';
import type { AdminDishDetail } from '@admin/shared/api';
import {
  NHAN_BUA_AN,
  NHAN_CACH_CHE_BIEN,
  NHAN_NGUON_MON,
  NHAN_NHIET_DO_MON,
  nhanTheoMa,
} from '@admin/shared/config';
import { ngayGioVN, safeHttpUrl } from '@admin/shared/lib';

/** Trần độ dài mô tả — khớp `DESCRIPTION_MAX_LENGTH` ở backend (domain/value_objects). */
const MO_TA_MAX = 1000;

/**
 * Mô tả món + nút sửa. Tách riêng vì nó có TRẠNG THÁI RIÊNG (đang sửa, đang lưu, lỗi),
 * không được làm bẩn phần còn lại của tab thông tin.
 *
 * Chữ đang gõ giữ trong state cục bộ và CHỈ gửi khi bấm Lưu, nên bộ gõ tiếng Việt không bị
 * ngắt giữa chừng (cùng lý do với ô tìm kiếm — xem `shared/ui/OTimKiem.tsx`).
 */
function KhoiMoTa({
  data,
  onLuu,
}: {
  data: AdminDishDetail;
  onLuu?: (text: string | null) => Promise<string | null>;
}) {
  const [dangSua, setDangSua] = useState(false);
  const [nhap, setNhap] = useState('');
  const [dangLuu, setDangLuu] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);

  const batDauSua = () => {
    setNhap(data.description ?? '');
    setLoi(null);
    setDangSua(true);
  };

  const luu = async (text: string | null) => {
    if (!onLuu) return;
    setDangLuu(true);
    const loiMoi = await onLuu(text);
    setDangLuu(false);
    if (loiMoi) setLoi(loiMoi);
    else setDangSua(false);
  };

  if (dangSua) {
    return (
      <div>
        <textarea
          className="o-nhap"
          rows={5}
          maxLength={MO_TA_MAX}
          value={nhap}
          onChange={(e) => setNhap(e.target.value)}
          aria-label="Mô tả món"
        />
        <p className="muted">
          {nhap.trim().length}/{MO_TA_MAX} ký tự. Để trống rồi lưu = gỡ bản sửa, trở về mô tả
          gốc.
        </p>
        {loi && <p className="notice notice--warn">{loi}</p>}
        <div>
          <button
            type="button"
            className="btn nut-chinh"
            onClick={() => luu(nhap)}
            disabled={dangLuu}
          >
            {dangLuu ? 'Đang lưu…' : 'Lưu'}
          </button>{' '}
          <button type="button" className="btn" onClick={() => setDangSua(false)} disabled={dangLuu}>
            Huỷ
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      {data.description ? (
        <p className="chi-tiet__mo-ta">{data.description}</p>
      ) : (
        <p className="muted">Chưa tra được giới thiệu cho món này.</p>
      )}
      {data.mo_ta_da_sua && (
        <p className="muted">Đang hiện bản do quản trị viên sửa tay (mô tả gốc đã được giữ nguyên).</p>
      )}
      {onLuu && (
        <div>
          <button type="button" className="btn" onClick={batDauSua}>
            Sửa mô tả
          </button>
          {data.mo_ta_da_sua && (
            <>
              {' '}
              <button type="button" className="btn" onClick={() => luu(null)} disabled={dangLuu}>
                Gỡ bản sửa
              </button>
            </>
          )}
          {loi && <p className="notice notice--warn">{loi}</p>}
        </div>
      )}
    </div>
  );
}

export function DishInfo({
  data,
  onLuuMoTa,
}: {
  data: AdminDishDetail;
  /** Có thì hiện nút sửa mô tả. Không có thì khối vẫn CHỈ ĐỌC như trước. */
  onLuuMoTa?: (text: string | null) => Promise<string | null>;
}) {
  // `match_keywords`/`meal_times` có `default_factory` ở backend nên kiểu sinh ra là
  // optional. Chuẩn hoá một lần ở đây thay vì rải `?? []` khắp phần dựng.
  const tuKhoa = data.match_keywords ?? [];
  const bua = data.meal_times ?? [];
  const nguonAnToan = safeHttpUrl(data.source_url);

  return (
    <div className="chi-tiet__than">
      <h4 className="chi-tiet__nhan">Giới thiệu</h4>
      <KhoiMoTa data={data} onLuu={onLuuMoTa} />

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

      {/* Chỉ http/https: `source_url` là dữ liệu nhập/cào, `javascript:` phải bị chặn. */}
      {nguonAnToan && (
        <p>
          <a className="linkish" href={nguonAnToan} target="_blank" rel="noopener noreferrer">
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
