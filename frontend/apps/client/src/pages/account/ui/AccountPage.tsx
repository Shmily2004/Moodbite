/**
 * TRANG TÀI KHOẢN — `/account`.
 *
 * Dựng theo bản thiết kế chủ dự án gửi 2026-08-22, nhưng CHỈ những mục có dữ liệu thật.
 *
 * ✅ ĐÃ DỰNG            | nguồn dữ liệu
 * ---------------------|--------------------------------------------------------------
 * Ảnh đại diện          | sinh từ tên, hoặc ảnh người dùng tải lên (lưu ở máy)
 * Tên · email · ngày TG | `GET /auth/me` (`to_self()` — chính chủ mới thấy email)
 * Món đã lưu            | localStorage (`features/save-dish`)
 * Đã xem gần đây        | localStorage (`features/recent-dishes`)
 * Sở thích của bạn      | localStorage, chọn từ ĐÚNG bộ lọc backend hiểu được
 * Cài đặt (nền, đăng xuất)
 *
 * ⛔ CHƯA DỰNG — chủ dự án đã đánh dấu "cần xem kỹ trước khi làm", và đúng là cả bốn đều
 *    CHƯA CÓ GÌ Ở BACKEND (chi tiết đã báo cáo riêng):
 *      - Viết review / "Đánh giá của tôi" (42)  -> chưa có endpoint ghi & đọc review
 *      - Cấp độ + huy hiệu                      -> cần đếm tương tác theo NGƯỜI, mà
 *                                                  `/interactions` hiện ghi theo PHIÊN
 *      - "Lượt khám phá" (128)                  -> cùng lý do trên
 *      - "Quán yêu thích" (15)                  -> mới lưu được MÓN, chưa lưu được QUÁN
 *    Vẽ ra mấy con số đó khi không đếm được là bịa số — đúng thứ CLAUDE.md mục 4 cấm.
 *
 * Chưa đăng nhập thì đá về trang đăng nhập: trang này không có gì để xem khi không biết
 * bạn là ai.
 */
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { SiteHeader } from '@/widgets/site-header';
import { AvatarPicker } from '@/features/change-avatar';
import { TastePicker } from '@/features/taste-preferences';
import { useSavedDishes } from '@/features/save-dish';
import { useRecentDishes } from '@/features/recent-dishes';
import { ThemeToggle } from '@/features/switch-theme';
import { useUserSessionContext } from '@/entities/user';
import { dishRoute, ROUTES } from '@/shared/config';

/** "05/2024" từ chuỗi ISO backend trả về. Sai định dạng thì thà không hiện gì. */
function thangNam(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  return `${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
}

export function AccountPage() {
  const session = useUserSessionContext();
  const navigate = useNavigate();
  const saved = useSavedDishes();
  const recent = useRecentDishes();

  if (!session.isLoggedIn) {
    return <Navigate to={ROUTES.login} replace />;
  }

  const ten = session.user?.display_name || session.user?.username || null;
  const thamGia = thangNam(session.user?.created_at);

  return (
    <div className="page">
      <SiteHeader />

      <main className="page__body account">
        {/* --- Thẻ đầu trang: ảnh đại diện + thông tin + số liệu --- */}
        <section className="account__head">
          <AvatarPicker name={ten} />

          <div className="account__id">
            <h1 className="account__name">{ten ?? '…'}</h1>
            <p className="account__line">@{session.user?.username}</p>
            {session.user?.email ? (
              <p className="account__line">{session.user.email}</p>
            ) : (
              /* Không có email thì nói rõ hệ quả, thay vì để trống cho người dùng đoán. */
              <p className="account__line account__line--warn">
                Chưa có email — bạn sẽ không tự lấy lại được mật khẩu nếu quên.
              </p>
            )}
            {thamGia && <p className="account__since">Thành viên từ {thamGia}</p>}
          </div>

          {/*
            CHỈ HAI Ô SỐ LIỆU. Bản thiết kế có bốn (thêm "Đánh giá" và "Lượt khám phá")
            nhưng hai cái đó chưa có gì để đếm — xem ghi chú đầu file.
          */}
          <ul className="account__stats">
            <li className="stat">
              <span className="stat__value">{saved.saved.length}</span>
              <span className="stat__label">Món đã lưu</span>
            </li>
            <li className="stat">
              <span className="stat__value">{recent.recent.length}</span>
              <span className="stat__label">Món đã xem</span>
            </li>
          </ul>
        </section>

        <TastePicker />

        {/* --- Món đã lưu --- */}
        <section className="account__block">
          <div className="results__head">
            <h2 className="section-title">
              <span aria-hidden="true">❤️</span> Món đã lưu
            </h2>
            {saved.saved.length > 0 && (
              <p className="results__count">{saved.saved.length} món</p>
            )}
          </div>

          {saved.saved.length === 0 ? (
            <p className="section-sub">
              Chưa lưu món nào. Bấm hình trái tim trên thẻ món ở{' '}
              <Link to={ROUTES.home}>trang chủ</Link> để lưu lại.
            </p>
          ) : (
            <>
              <p className="section-sub">
                Lưu trên máy này. Đổi máy hoặc xoá dữ liệu trình duyệt là mất.
              </p>
              <ul className="chip-row">
                {saved.saved.map((mon) => (
                  <li key={mon.dishId}>
                    <button
                      type="button"
                      className="chip"
                      onClick={() => navigate(dishRoute(mon.dishId))}
                    >
                      {mon.name}
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>

        {/* --- Đã xem gần đây --- */}
        <section className="account__block">
          <div className="results__head">
            <h2 className="section-title">
              <span aria-hidden="true">🕘</span> Đã xem gần đây
            </h2>
            {recent.recent.length > 0 && (
              <button type="button" className="linkish" onClick={recent.clear}>
                Xoá lịch sử
              </button>
            )}
          </div>

          {recent.recent.length === 0 ? (
            <p className="section-sub">Chưa mở món nào.</p>
          ) : (
            <ul className="chip-row">
              {recent.recent.map((mon) => (
                <li key={mon.dishId}>
                  <button
                    type="button"
                    className="chip"
                    onClick={() => navigate(dishRoute(mon.dishId))}
                  >
                    {mon.name}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* --- Cài đặt --- */}
        <section className="account__block">
          <h2 className="section-title">
            <span aria-hidden="true">⚙️</span> Cài đặt
          </h2>
          <div className="account__settings">
            <div className="account__setting">
              <span>Giao diện nền tối</span>
              <ThemeToggle />
            </div>
            <div className="account__setting">
              <span>Đăng xuất khỏi máy này</span>
              <button
                type="button"
                className="btn btn--sm"
                onClick={() => {
                  session.logout();
                  navigate(ROUTES.home);
                }}
              >
                Đăng xuất
              </button>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
