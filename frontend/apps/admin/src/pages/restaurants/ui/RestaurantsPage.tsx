/**
 * Trang quản lý quán — tầng `pages`: GHÉP feature lại, giữ state điều phối.
 *
 * KHÔNG còn nhận props: từ khi có router, trang là route con của `AdminLayout` nên
 * không có component cha để truyền props xuống. Phiên đăng nhập lấy qua context.
 * Nút đăng xuất đã chuyển lên `AdminLayout` — nó thuộc về khung, không thuộc về trang.
 */
import { useAdminSessionContext } from '@/features/admin-login';
import {
  AddRestaurantForm,
  RestaurantRow,
  useRestaurantAdmin,
} from '@/features/manage-restaurants';

/** Nhãn tiếng Việt cho `?loc=`. Khoá do backend đặt — xem `data_quality.py`. */
const NHAN_LOC: Record<string, string> = {
  dong_tam: 'Quán có khả năng đã đóng cửa',
  thieu_lien_he: 'Quán không có cách nào liên hệ',
};

export function RestaurantsPage() {
  const session = useAdminSessionContext();
  const admin = useRestaurantAdmin({ onExpired: session.handleExpired });

  return (
    <div className="page">
      <div className="page__intro">
        <h2>Quản lý quán</h2>
        <p className="muted small">
          Ẩn quán để nó biến mất khỏi tìm kiếm của người dùng. Dữ liệu KHÔNG bị xoá —
          bỏ ẩn lúc nào cũng được.
        </p>
      </div>

      {/* Đang xem một danh sách ĐÃ LỌC (bấm từ hộp "Cần xử lý" ở trang Tổng quan).
          Phải nói rõ, nếu không người quản trị tưởng cả dataset chỉ có ngần này quán. */}
      {admin.loc && (
        <p className="notice">
          Đang lọc: <strong>{NHAN_LOC[admin.loc] ?? admin.loc}</strong>{' '}
          <button type="button" className="linkish" onClick={admin.clearLoc}>
            bỏ lọc
          </button>
        </p>
      )}

      <div className="bang__loc">
        <input
          className="o-nhap"
          placeholder="Tìm theo tên, địa chỉ hoặc placeId…"
          value={admin.query}
          onChange={(event) => admin.setQuery(event.target.value)}
        />
        <label className="check">
          <input
            type="checkbox"
            checked={admin.includeHidden}
            onChange={(event) => admin.setIncludeHidden(event.target.checked)}
          />
          Hiện cả quán đã ẩn
        </label>
        <AddRestaurantForm onCreate={admin.createRestaurant} />
      </div>

      {admin.error && <p className="error">{admin.error}</p>}
      {admin.notice && !admin.error && <p className="notice">{admin.notice}</p>}
      {admin.loading && <p className="muted">Đang tải…</p>}

      {!admin.loading && admin.restaurants.length === 0 && (
        <p className="muted">Không có quán nào khớp.</p>
      )}

      {admin.restaurants.length > 0 && (
        <>
          <p className="muted small">Đang hiển thị {admin.total} quán.</p>
          <div className="bang-cuon">
            <table className="bang">
              <thead>
                <tr>
                  <th scope="col">Quán</th>
                  <th scope="col">Loại hình</th>
                  <th scope="col">Đánh giá</th>
                  <th scope="col">Trạng thái</th>
                  <th scope="col">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {admin.restaurants.map((restaurant) => (
                  <RestaurantRow
                    key={restaurant.restaurant_id ?? restaurant.name}
                    restaurant={restaurant}
                    onToggleHidden={(r) => void admin.toggleHidden(r)}
                    onSave={admin.saveChanges}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
