/**
 * TRANG QUẢN LÝ MÓN ĂN — khoảng trống rõ nhất của khu quản trị trước 2026-08-26.
 *
 * Dựng theo `frontend/design/Dashboard admin.png` (mục "Quản lý món ăn" trên menu):
 *
 *   855 món
 *   [🔎 Tìm món…]   [Tất cả] [Có quán] [Chưa có quán] [Thiếu ảnh] [Thiếu mô tả]
 *   Ảnh · Tên món · Ẩm thực · Mô tả · Trạng thái
 *
 * ⚠️ KHÔNG CÓ CỘT ĐÁNH GIÁ. Món KHÔNG có trường rating — chỉ QUÁN mới có, và chỉ 2,2%
 * quán có. Chủ dự án cũng chốt đúng điều này khi bàn về Admin (2026-08-26).
 *
 * ⚠️ CHỈ ĐỌC, và đây là hạn chế THẬT chứ không phải làm dở: `dish_catalog.json` là file
 * do `scripts/build_dish_catalog.py` SINH RA, nên sửa qua giao diện sẽ bị lần chạy sau
 * xoá sạch. Muốn sửa được thì phải chuyển danh mục món sang SQLite trước. Trang nói
 * thẳng điều đó thay vì bày ra nút "Sửa" rồi báo lỗi.
 */
import { useDishAdmin } from '@/features/manage-dishes';
import type { AdminDishRow, LocMon } from '@/shared/api';

const BO_LOC: { khoa: LocMon; nhan: string }[] = [
  { khoa: 'all', nhan: 'Tất cả' },
  { khoa: 'with_restaurants', nhan: 'Có quán' },
  { khoa: 'without_restaurants', nhan: 'Chưa có quán' },
  { khoa: 'missing_image', nhan: 'Thiếu ảnh' },
  { khoa: 'missing_description', nhan: 'Thiếu mô tả' },
];

export function DishesPage() {
  const { rows, total, query, setQuery, filter, setFilter, loading, error } =
    useDishAdmin();

  return (
    <section className="panel">
      <div className="bang__dau">
        <h2 className="panel__tieu-de">Quản lý món ăn</h2>
        <p className="muted">
          {loading ? 'Đang tìm…' : `${total.toLocaleString('vi-VN')} món khớp bộ lọc`}
          {!loading && rows.length < total && ` — đang hiện ${rows.length} món đầu`}
        </p>
      </div>

      <div className="bang__loc">
        <input
          className="o-nhap"
          type="search"
          placeholder="Tìm theo tên hoặc mã món…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Tìm món"
        />
        <div className="chip-hang" role="group" aria-label="Lọc món">
          {BO_LOC.map((b) => (
            <button
              key={b.khoa}
              type="button"
              className={filter === b.khoa ? 'chip chip--dang' : 'chip'}
              aria-pressed={filter === b.khoa}
              onClick={() => setFilter(b.khoa)}
            >
              {b.nhan}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="notice notice--warn">{error}</p>}

      {!loading && rows.length === 0 && !error && (
        <p className="muted">Không có món nào khớp. Thử bỏ bớt bộ lọc.</p>
      )}

      {rows.length > 0 && (
        <div className="bang-cuon">
          <table className="bang">
            <thead>
              <tr>
                <th scope="col">Ảnh</th>
                <th scope="col">Tên món</th>
                <th scope="col">Ẩm thực</th>
                <th scope="col">Mô tả</th>
                <th scope="col">Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((d) => (
                <DongMon key={d.dish_id} mon={d} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="muted panel__ghi-chu">
        Chỉ xem, chưa sửa được: danh mục món là file do <code>build_dish_catalog.py</code>{' '}
        sinh ra, sửa qua đây sẽ bị lần chạy sau ghi đè.
      </p>
    </section>
  );
}

function DongMon({ mon }: { mon: AdminDishRow }) {
  return (
    <tr>
      <td>
        {mon.image_url ? (
          <img
            className="o-anh"
            src={mon.image_url}
            alt=""
            loading="lazy"
            // Ảnh lấy từ Wikimedia — link ngoài có thể chết. Hỏng thì ẩn đi, để lộ nền ô
            // thay vì hiện biểu tượng ảnh vỡ của trình duyệt.
            onError={(e) => {
              e.currentTarget.style.display = 'none';
            }}
          />
        ) : (
          <span className="o-anh o-anh--trong" aria-label="Chưa có ảnh">
            —
          </span>
        )}
      </td>
      <td>
        <span className="bang__ten">{mon.name}</span>
        <br />
        <code className="muted bang__ma">{mon.dish_id}</code>
        {/* Nhãn DANH MỤC quan trọng với admin: "Bún" không phải món, nên nó không xuất
            hiện trong lưới gợi ý của người dùng dù vẫn nằm trong danh mục. */}
        {mon.is_category && <span className="nhan nhan--tin">danh mục</span>}
      </td>
      <td className="muted">{mon.cuisine || '—'}</td>
      <td>{mon.has_description ? '✓' : <span className="thieu">thiếu</span>}</td>
      <td>
        {mon.is_active ? (
          <span className="nhan nhan--ok">Có quán</span>
        ) : (
          <span className="nhan nhan--tat">Chưa có quán</span>
        )}
      </td>
    </tr>
  );
}
