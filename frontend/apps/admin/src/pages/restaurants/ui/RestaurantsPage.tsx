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

      <div className="toolbar">
        <input
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
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Quán</th>
                  <th>Loại hình</th>
                  <th>Đánh giá</th>
                  <th>Trạng thái</th>
                  <th>Thao tác</th>
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
