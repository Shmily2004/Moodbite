/**
 * TRANG QUẢN LÝ QUÁN ĂN — tầng `pages`: GHÉP feature lại.
 *
 * Dựng theo `frontend/design/restaurant manager admin.png` (2026-09-16):
 *
 *   Quản lý quán ăn                                              [+ Thêm quán mới]
 *   [Tổng 52.854] [Đang hiển thị] [Đã ẩn] [Nhập tay] | Khu vực ▾  Nguồn ▾  Trạng thái ▾
 *                                                    | [Tìm…]               [Xoá bộ lọc]
 *   Tab: Tất cả · Đang hiển thị · Đã ẩn · Nhập tay   (kèm số)
 *   ☐ Quán ăn · Địa chỉ · Khu vực · Rating · Đánh giá · Nguồn · Trạng thái · Cập nhật · Thao tác
 *   Đã chọn N quán [Ẩn quán] [Hiển thị]      ‹ 1 2 … ›      [20 / trang]
 *
 * ⚠️ KHÁC BẢN THIẾT KẾ, CÓ LÝ DO:
 *   - Không có nhãn "Nổi bật": dự án không có khái niệm quán nổi bật.
 *   - Không có menu "…" trên từng dòng: thao tác thật chỉ có Sửa và Ẩn/Bỏ ẩn, để thẳng ra.
 *   - "Cập nhật lần cuối" là ngày NGUỒN cập nhật bản ghi (có ở ~36% quán, đo 2026-09-16);
 *     không có thì "—".
 *   - "Chọn tất cả" chỉ chọn TRANG ĐANG XEM, không phải 52.854 quán.
 */
import { useAdminSessionContext } from '@/features/admin-login';
import {
  AddRestaurantForm,
  RestaurantRow,
  useRestaurantAdmin,
  type BoLocQuan,
} from '@/features/manage-restaurants';
import { NHAN_NGUON_QUAN, nhanTheoMa } from '@/shared/config';
import { phanTramVN, soVN } from '@/shared/lib';
import { PhanTrang } from '@/shared/ui';

/** Nhãn tiếng Việt cho `?loc=`. Khoá do backend đặt — xem `data_quality.py`. */
const NHAN_LOC: Record<string, string> = {
  dong_tam: 'Quán có khả năng đã đóng cửa',
  thieu_lien_he: 'Quán không có cách nào liên hệ',
};

type KhoaTab = 'tat-ca' | 'hien' | 'an' | 'tay';

/** Tab là LỐI TẮT của hai ô chọn Trạng thái + Nguồn, không phải bộ lọc thứ ba. */
const TAB: Record<KhoaTab, Pick<BoLocQuan, 'status' | 'source'>> = {
  'tat-ca': { status: null, source: null },
  hien: { status: 'visible', source: null },
  an: { status: 'hidden', source: null },
  tay: { status: null, source: 'manual' },
};

function tabDangChon(f: BoLocQuan): KhoaTab | null {
  const khop = (Object.keys(TAB) as KhoaTab[]).find(
    (k) => TAB[k].status === f.status && TAB[k].source === f.source,
  );
  return khop ?? null;
}

export function RestaurantsPage() {
  const session = useAdminSessionContext();
  const a = useRestaurantAdmin({ onExpired: session.handleExpired });
  const st = a.stats;
  const tab = tabDangChon(a.filters);
  const coLoc = Boolean(
    a.filters.q || a.filters.district || a.filters.source || a.filters.status || a.filters.loc,
  );
  const maTrang = a.restaurants.map((r) => r.restaurant_id).filter(Boolean) as string[];
  const chonHetTrang = maTrang.length > 0 && maTrang.every((m) => a.selected.has(m));

  return (
    <div className="trang-quan-ly">
      <header className="trang-quan-ly__dau">
        <div>
          <h2 className="tong-quan__chao">Quản lý quán ăn</h2>
          <p className="muted">
            Ẩn quán để nó biến mất khỏi tìm kiếm của người dùng. Dữ liệu KHÔNG bị xoá — bỏ
            ẩn lúc nào cũng được.
          </p>
        </div>
      </header>

      <AddRestaurantForm onCreate={a.createRestaurant} />

      <section className="panel quan-bo-loc">
        {st && (
          <ul className="the-so the-so--gon" aria-label="Tổng hợp quán">
            <TheSo nhan="Tổng số quán" so={st.total} phu="toàn bộ dữ liệu" />
            <TheSo nhan="Đang hiển thị" so={st.visible} phu={phanTramVN(st.visible, st.total)} />
            <TheSo nhan="Đã ẩn" so={st.hidden} phu={phanTramVN(st.hidden, st.total)} />
            <TheSo nhan="Nhập tay" so={st.manual} phu={phanTramVN(st.manual, st.total)} />
          </ul>
        )}

        <div className="quan-bo-loc__o">
          <label className="o-truong">
            <span className="small muted">Khu vực</span>
            <select
              className="o-chon"
              value={a.filters.district ?? ''}
              onChange={(e) => a.setFilters({ district: e.target.value || null })}
            >
              <option value="">Tất cả khu vực</option>
              {st?.districts.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.value} ({soVN(d.count)})
                </option>
              ))}
            </select>
          </label>
          <label className="o-truong">
            <span className="small muted">Nguồn dữ liệu</span>
            <select
              className="o-chon"
              value={a.filters.source ?? ''}
              onChange={(e) => a.setFilters({ source: e.target.value || null })}
            >
              <option value="">Tất cả nguồn</option>
              {st?.sources.map((s) => (
                <option key={s.value} value={s.value}>
                  {nhanTheoMa(NHAN_NGUON_QUAN, s.value)} ({soVN(s.count)})
                </option>
              ))}
              {/* "Nhập tay" luôn chọn được, kể cả khi CHƯA có quán nhập tay nào — lúc đó
                  kết quả rỗng là câu trả lời đúng. */}
              {st && !st.sources.some((s) => s.value === 'manual') && (
                <option value="manual">Nhập tay (0)</option>
              )}
            </select>
          </label>
          <label className="o-truong">
            <span className="small muted">Trạng thái</span>
            <select
              className="o-chon"
              value={a.filters.status ?? ''}
              onChange={(e) =>
                a.setFilters({
                  status: (e.target.value || null) as BoLocQuan['status'],
                })
              }
            >
              <option value="">Tất cả trạng thái</option>
              <option value="visible">Đang hiển thị</option>
              <option value="hidden">Đã ẩn</option>
            </select>
          </label>
          <input
            className="o-nhap"
            placeholder="Tìm theo tên, địa chỉ hoặc placeId…"
            value={a.filters.q}
            onChange={(e) => a.setQuery(e.target.value)}
            aria-label="Tìm quán"
          />
          <button type="button" className="ghost" onClick={a.clearFilters} disabled={!coLoc}>
            Xoá bộ lọc
          </button>
        </div>
      </section>

      {/* Đang xem một danh sách ĐÃ LỌC (bấm từ hộp "Cần xử lý" ở trang Tổng quan).
          Phải nói rõ, nếu không người quản trị tưởng cả dataset chỉ có ngần này quán. */}
      {a.loc && (
        <p className="notice">
          Đang lọc: <strong>{NHAN_LOC[a.loc] ?? a.loc}</strong>{' '}
          <button type="button" className="linkish" onClick={a.clearLoc}>
            bỏ lọc
          </button>
        </p>
      )}

      <nav className="tab-loc" aria-label="Lọc nhanh theo trạng thái">
        {(
          [
            ['tat-ca', 'Tất cả', st?.total],
            ['hien', 'Đang hiển thị', st?.visible],
            ['an', 'Đã ẩn', st?.hidden],
            ['tay', 'Nhập tay', st?.manual],
          ] as Array<[KhoaTab, string, number | undefined]>
        ).map(([khoa, nhan, so]) => (
          <button
            key={khoa}
            type="button"
            className={tab === khoa ? 'tab-loc__nut tab-loc__nut--dang' : 'tab-loc__nut'}
            aria-pressed={tab === khoa}
            onClick={() => a.setFilters(TAB[khoa])}
          >
            {nhan}
            {so != null && <span className="chip__so">{soVN(so)}</span>}
          </button>
        ))}
      </nav>

      {a.error && <p className="error">{a.error}</p>}
      {a.notice && !a.error && <p className="notice">{a.notice}</p>}
      {a.loading && a.restaurants.length === 0 && <p className="muted">Đang tải…</p>}

      {!a.loading && a.restaurants.length === 0 && !a.error && (
        <p className="muted">Không có quán nào khớp bộ lọc.</p>
      )}

      {a.restaurants.length > 0 && (
        <section className="panel">
          <div className="bang-cuon" aria-busy={a.loading}>
            <table className="bang">
              <thead>
                <tr>
                  <th scope="col">
                    <input
                      type="checkbox"
                      checked={chonHetTrang}
                      onChange={a.toggleSelectAllOnPage}
                      aria-label="Chọn tất cả quán trên trang này"
                    />
                  </th>
                  <th scope="col">Quán ăn</th>
                  <th scope="col">Địa chỉ</th>
                  <th scope="col">Khu vực</th>
                  <th scope="col">Rating</th>
                  <th scope="col">Đánh giá</th>
                  <th scope="col">Nguồn</th>
                  <th scope="col">Trạng thái</th>
                  <th scope="col">Cập nhật lần cuối</th>
                  <th scope="col">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {a.restaurants.map((r) => (
                  <RestaurantRow
                    key={r.restaurant_id ?? r.name}
                    restaurant={r}
                    selected={!!r.restaurant_id && a.selected.has(r.restaurant_id)}
                    onToggleSelected={a.toggleSelected}
                    onToggleHidden={(x) => void a.toggleHidden(x)}
                    onSave={a.saveChanges}
                  />
                ))}
              </tbody>
            </table>
          </div>

          <div className="thanh-hang-loat">
            <span className="small">Đã chọn {soVN(a.selected.size)} quán</span>
            <button
              type="button"
              className="ghost"
              disabled={a.selected.size === 0 || a.bulkBusy}
              onClick={() => void a.bulkSetVisibility(false)}
            >
              Ẩn quán
            </button>
            <button
              type="button"
              className="ghost"
              disabled={a.selected.size === 0 || a.bulkBusy}
              onClick={() => void a.bulkSetVisibility(true)}
            >
              Hiển thị
            </button>
          </div>

          <PhanTrang
            trang={a.page}
            coTrang={a.pageSize}
            tong={a.total}
            donVi="quán"
            onDoiTrang={a.setPage}
            onDoiCoTrang={a.setPageSize}
          />
        </section>
      )}
    </div>
  );
}

function TheSo({ nhan, so, phu }: { nhan: string; so: number; phu: string }) {
  return (
    <li className="the-so__o">
      <span className="the-so__nhan">{nhan}</span>
      <span className="the-so__gia-tri">{soVN(so)}</span>
      <span className="muted the-so__phu">{phu}</span>
    </li>
  );
}
