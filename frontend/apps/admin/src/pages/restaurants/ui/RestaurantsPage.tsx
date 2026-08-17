/**
 * Trang quản lý quán — tầng `pages`: GHÉP feature lại, giữ state điều phối.
 *
 * Component "thông minh" duy nhất của app admin. Mọi thứ bên dưới nhận props.
 */
import { RestaurantRow, useRestaurantAdmin } from '@/features/manage-restaurants';

export interface RestaurantsPageProps {
  onExpired: () => void;
  onLogout: () => void;
}

export function RestaurantsPage({ onExpired, onLogout }: RestaurantsPageProps) {
  const admin = useRestaurantAdmin({ onExpired });

  return (
    <div className="page">
      <header className="topbar">
        <div>
          <h1>Quản lý quán</h1>
          <p className="muted small">
            Ẩn quán để nó biến mất khỏi tìm kiếm của người dùng. Dữ liệu KHÔNG bị xoá —
            bỏ ẩn lúc nào cũng được.
          </p>
        </div>
        <button className="ghost" onClick={onLogout}>
          Đăng xuất
        </button>
      </header>

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
