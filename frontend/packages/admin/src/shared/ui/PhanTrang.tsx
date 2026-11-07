/**
 * Thanh PHÂN TRANG dùng chung: "Hiển thị 1–20 của 855 món" · nút trang · số dòng/trang.
 *
 * Chỉ là VIEW: trang hiện tại và số dòng/trang do ViewModel giữ (thường là trên URL).
 */
import { danhSachTrang, soVN } from '../lib';

export interface PhanTrangProps {
  trang: number;
  coTrang: number;
  tong: number;
  /** Danh từ đếm: "món", "quán". */
  donVi: string;
  onDoiTrang: (trang: number) => void;
  onDoiCoTrang?: (co: number) => void;
  cacCoTrang?: number[];
}

export function PhanTrang({
  trang,
  coTrang,
  tong,
  donVi,
  onDoiTrang,
  onDoiCoTrang,
  cacCoTrang = [10, 20, 50, 100],
}: PhanTrangProps) {
  const tongTrang = Math.max(1, Math.ceil(tong / coTrang));
  const dau = tong === 0 ? 0 : (trang - 1) * coTrang + 1;
  const cuoi = Math.min(tong, trang * coTrang);

  return (
    <div className="phan-trang">
      <p className="muted small phan-trang__dem">
        Hiển thị {soVN(dau)}–{soVN(cuoi)} của {soVN(tong)} {donVi}
      </p>
      <nav className="phan-trang__nut" aria-label="Phân trang">
        <button
          type="button"
          className="ghost"
          disabled={trang <= 1}
          onClick={() => onDoiTrang(trang - 1)}
          aria-label="Trang trước"
        >
          ‹
        </button>
        {danhSachTrang(trang, tongTrang).map((t, i) =>
          t === '…' ? (
            <span key={`cham-${i}`} className="muted phan-trang__cham">
              …
            </span>
          ) : (
            <button
              key={t}
              type="button"
              className={t === trang ? 'phan-trang__so' : 'ghost phan-trang__so'}
              aria-current={t === trang ? 'page' : undefined}
              onClick={() => onDoiTrang(t)}
            >
              {t}
            </button>
          ),
        )}
        <button
          type="button"
          className="ghost"
          disabled={trang >= tongTrang}
          onClick={() => onDoiTrang(trang + 1)}
          aria-label="Trang sau"
        >
          ›
        </button>
      </nav>
      {onDoiCoTrang && (
        <select
          className="o-chon"
          value={coTrang}
          onChange={(e) => onDoiCoTrang(Number(e.target.value))}
          aria-label="Số dòng mỗi trang"
        >
          {cacCoTrang.map((c) => (
            <option key={c} value={c}>
              {c} / trang
            </option>
          ))}
        </select>
      )}
    </div>
  );
}
