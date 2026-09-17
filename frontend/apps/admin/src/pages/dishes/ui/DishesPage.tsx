/**
 * TRANG QUẢN LÝ MÓN ĂN.
 *
 * Dựng theo `frontend/design/dish management admin.png`:
 *
 *   Quản lý món ăn                         [Tổng số món 855] [Món có quán 298 (34,9%) ◔]
 *   [Tất cả 855] [Có quán 298] [Chưa có quán 557] [Thiếu ảnh] [Thiếu mô tả]  [🔎 Tìm]
 *   Món ăn · Mô tả · Có quán · Nguồn mô tả · Ảnh · Trạng thái · Cập nhật · Thao tác
 *   Hiển thị 1–20 của 855 món          ‹ 1 2 3 … 43 ›          [20 / trang]
 *
 * ⚠️ KHÁC BẢN THIẾT KẾ, CÓ LÝ DO:
 *   - KHÔNG có nút "Thêm món mới", "Bộ lọc" nâng cao, nút sửa (✎) và menu "…" trên từng
 *     dòng. Danh mục món là file do `build_dish_catalog.py` SINH RA — sửa qua đây sẽ bị
 *     lần chạy sau ghi đè. Bày nút ra rồi báo lỗi còn tệ hơn là nói thẳng.
 *   - "Nguồn mô tả" hiện NGUỒN THẬT (Wikipedia / Wikidata / Nhập tay / Suy từ tên quán),
 *     không có nhãn "AI đề xuất" nào vì dự án không sinh mô tả bằng AI.
 *   - "Cập nhật" chỉ có ở 126/855 món (đo 2026-09-16). Món không có ngày hiện "—",
 *     KHÔNG thay bằng ngày dựng danh mục.
 *
 * Bấm "Xem chi tiết" -> sang TRANG RIÊNG `/mon-an/:dishId` (trước là ô trượt bên cạnh).
 */
import { Link } from 'react-router-dom';
import { useDishAdmin } from '@/features/manage-dishes';
import type { AdminDishRow, LocMon } from '@/shared/api';
import { NHAN_NGUON_MON, duongDanMon, nhanTheoMa } from '@/shared/config';
import { ngayGioVN, phanTramVN, soVN } from '@/shared/lib';
import { PhanTrang, VongTienDo } from '@/shared/ui';

const BO_LOC: { khoa: LocMon; nhan: string }[] = [
  { khoa: 'all', nhan: 'Tất cả' },
  { khoa: 'with_restaurants', nhan: 'Có quán' },
  { khoa: 'without_restaurants', nhan: 'Chưa có quán' },
  { khoa: 'missing_image', nhan: 'Thiếu ảnh' },
  { khoa: 'missing_description', nhan: 'Thiếu mô tả' },
];

export function DishesPage() {
  const m = useDishAdmin();

  return (
    <div className="trang-quan-ly">
      <header className="trang-quan-ly__dau">
        <div>
          <h2 className="tong-quan__chao">Quản lý món ăn</h2>
          <p className="muted">Quản lý toàn bộ danh mục món ăn trong hệ thống.</p>
        </div>
        {m.dishesTotal != null && (
          <ul className="the-so the-so--gon" aria-label="Tổng hợp món">
            <li className="the-so__o">
              <span className="the-so__nhan">Tổng số món</span>
              <span className="the-so__gia-tri">{soVN(m.dishesTotal)}</span>
            </li>
            <li className="the-so__o the-so__o--vong">
              <div>
                <span className="the-so__nhan">Món có quán tại Hà Nội</span>
                <span className="the-so__gia-tri">
                  {soVN(m.dishesWithRestaurants ?? 0)}{' '}
                  <span className="the-so__phu">
                    ({phanTramVN(m.dishesWithRestaurants ?? 0, m.dishesTotal)})
                  </span>
                </span>
              </div>
              <VongTienDo
                phan={m.dishesWithRestaurants ?? 0}
                tong={m.dishesTotal}
                nhan={`${phanTramVN(m.dishesWithRestaurants ?? 0, m.dishesTotal)} món có quán`}
              />
            </li>
          </ul>
        )}
      </header>

      <section className="panel">
        <div className="bang__loc">
          <div className="chip-hang" role="group" aria-label="Lọc món">
            {BO_LOC.map((b) => (
              <button
                key={b.khoa}
                type="button"
                className={m.filter === b.khoa ? 'chip chip--dang' : 'chip'}
                aria-pressed={m.filter === b.khoa}
                onClick={() => m.setFilter(b.khoa)}
              >
                {b.nhan}
                {m.counts[b.khoa] != null && (
                  <span className="chip__so">{soVN(m.counts[b.khoa] ?? 0)}</span>
                )}
              </button>
            ))}
          </div>
          <input
            className="o-nhap"
            type="search"
            placeholder="Tìm theo tên hoặc mã món…"
            value={m.query}
            onChange={(e) => m.setQuery(e.target.value)}
            aria-label="Tìm món"
          />
        </div>

        {m.error && <p className="notice notice--warn">{m.error}</p>}
        {m.loading && m.rows.length === 0 && <p className="muted">Đang tải…</p>}

        {!m.loading && m.rows.length === 0 && !m.error && (
          <p className="muted">Không có món nào khớp. Thử bỏ bớt bộ lọc.</p>
        )}

        {m.rows.length > 0 && (
          <div className="bang-cuon" aria-busy={m.loading}>
            <table className="bang">
              <thead>
                <tr>
                  <th scope="col">Món ăn</th>
                  <th scope="col">Mô tả</th>
                  <th scope="col" className="tnum">
                    Có quán
                  </th>
                  <th scope="col">Nguồn mô tả</th>
                  <th scope="col">Ảnh</th>
                  <th scope="col">Trạng thái</th>
                  <th scope="col">Cập nhật</th>
                  <th scope="col">
                    <span className="sr-only">Thao tác</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {m.rows.map((d) => (
                  <DongMon key={d.dish_id} mon={d} />
                ))}
              </tbody>
            </table>
          </div>
        )}

        {m.total > 0 && (
          <PhanTrang
            trang={m.page}
            coTrang={m.pageSize}
            tong={m.total}
            donVi="món"
            onDoiTrang={m.setPage}
            onDoiCoTrang={m.setPageSize}
          />
        )}

        <p className="muted panel__ghi-chu">
          Chỉ xem, chưa sửa được: danh mục món là file do <code>build_dish_catalog.py</code>{' '}
          sinh ra, sửa qua đây sẽ bị lần chạy sau ghi đè. "Có quán" đếm theo TÊN QUÁN khớp món
          — không phải thực đơn thật.
        </p>
      </section>
    </div>
  );
}

function DongMon({ mon }: { mon: AdminDishRow }) {
  return (
    <tr>
      <td>
        <div className="o-mon">
          {mon.image_url ? (
            <img
              className="o-anh"
              src={mon.image_url}
              alt=""
              loading="lazy"
              // Ảnh lấy từ Wikimedia — link ngoài có thể chết. Hỏng thì ẩn đi.
              onError={(e) => {
                e.currentTarget.style.display = 'none';
              }}
            />
          ) : (
            <span className="o-anh o-anh--trong" aria-hidden="true">
              —
            </span>
          )}
          <div>
            <Link className="bang__ten bang__ten-link" to={duongDanMon(mon.dish_id)}>
              {mon.name}
            </Link>
            <span className="bang__phu muted small">
              {mon.cuisine || 'chưa rõ ẩm thực'}
              {/* "Bún" là DANH MỤC, không phải món — không xuất hiện trong lưới gợi ý
                  của người dùng dù vẫn nằm trong danh mục. */}
              {mon.is_category && <span className="nhan nhan--tin">danh mục</span>}
            </span>
          </div>
        </div>
      </td>
      <td className="o-mo-ta">
        {mon.description ? (
          <span className="cat-dong" title={mon.description}>
            {mon.description}
          </span>
        ) : (
          <span className="thieu">thiếu mô tả</span>
        )}
      </td>
      <td className="tnum">
        {/* `null` = chỉ mục chưa lắp ở server, KHÔNG phải 0 quán. */}
        {mon.restaurant_count == null ? (
          <span className="muted">—</span>
        ) : (
          <span className={mon.restaurant_count === 0 ? 'thieu' : 'bang__ten'}>
            {soVN(mon.restaurant_count)}
            <span className="muted small"> quán</span>
          </span>
        )}
      </td>
      <td className="small">{nhanTheoMa(NHAN_NGUON_MON, mon.source)}</td>
      <td>
        {mon.image_url ? (
          <span className="nhan nhan--ok">có</span>
        ) : (
          <span className="nhan nhan--canh-bao">thiếu</span>
        )}
      </td>
      <td>
        {mon.is_active ? (
          <span className="nhan nhan--ok">Có quán</span>
        ) : (
          <span className="nhan nhan--tat">Chưa có quán</span>
        )}
      </td>
      <td className="small muted">{ngayGioVN(mon.last_updated)}</td>
      <td>
        <Link className="linkish" to={duongDanMon(mon.dish_id)} aria-label={`Xem chi tiết ${mon.name}`}>
          Xem chi tiết →
        </Link>
      </td>
    </tr>
  );
}
