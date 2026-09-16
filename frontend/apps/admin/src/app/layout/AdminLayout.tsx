/**
 * LAYOUT của app quản trị — khung dùng chung cho mọi trang SAU KHI đăng nhập.
 *
 * Dựng theo `frontend/design/Dashboard admin.png` (chủ dự án gửi 2026-08-26):
 * CỘT TRÁI cố định (logo + menu) và thanh trên mỏng (tên trang + tài khoản).
 *
 * Trước đó điều hướng nằm trên một thanh ngang. Đổi sang cột trái vì bản thiết kế có 7
 * mục menu — hàng ngang 7 mục sẽ tràn ngay ở màn hình laptop, và khu quản trị vốn là
 * màn hình rộng dùng trên máy tính.
 *
 * TOÀN BỘ 8 MỤC NAY ĐỀU CHẠY THẬT (2026-09-08). Trước đó "Chất lượng dữ liệu" hiện mờ
 * kèm chữ "chưa dựng"; nay đã có trang thật, và có thêm "Cần xử lý" theo bản thiết kế
 * `frontend/design/needs to be handled admin.png`.
 *
 * Cơ chế `chuaDung` (hiện mờ, không bấm được) VẪN GIỮ LẠI dù hiện không mục nào dùng:
 * nó là cách đúng để thêm một mục đã có bản vẽ nhưng chưa có trang. Link chết thì người
 * dùng bấm vào gặp 404 và không hiểu vì sao; giấu hẳn thì không ai biết kế hoạch tới đâu.
 */
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useAdminSessionContext } from '@/features/admin-login';
import { ROUTES } from '@/shared/config';

interface MucMenu {
  duongDan: string;
  nhan: string;
  /** Chưa dựng -> hiện mờ, không bấm được. */
  chuaDung?: boolean;
}

/** Thứ tự đúng như bản thiết kế, kể cả mục chưa dựng. */
const MENU: MucMenu[] = [
  { duongDan: ROUTES.overview, nhan: 'Tổng quan' },
  { duongDan: ROUTES.dishes, nhan: 'Quản lý món ăn' },
  { duongDan: ROUTES.restaurants, nhan: 'Quản lý quán ăn' },
  { duongDan: ROUTES.quality, nhan: 'Chất lượng dữ liệu' },
  { duongDan: ROUTES.issues, nhan: 'Cần xử lý' },
  { duongDan: ROUTES.recommendation, nhan: 'Gợi ý & Hệ thống' },
  { duongDan: ROUTES.activity, nhan: 'Nhật ký hoạt động' },
  { duongDan: ROUTES.system, nhan: 'Cài đặt hệ thống' },
];

/** Tên trang hiện lên thanh đầu — suy từ đường dẫn, không truyền qua từng trang. */
function tenTrang(duongDan: string): string {
  // Suy từ MENU thay vì viết lại danh sách: thêm trang mới chỉ phải sửa MENU, không thể
  // quên cập nhật tên trên thanh đầu.
  const muc = MENU.find((m) => !m.chuaDung && m.duongDan === duongDan);
  return muc?.nhan ?? 'Quản trị';
}

export function AdminLayout() {
  const session = useAdminSessionContext();
  const location = useLocation();

  return (
    <div className="quan-tri">
      <aside className="canh-trai">
        <div className="canh-trai__hieu">
          <img src="/anh/logo.png" alt="MoodBite" className="canh-trai__logo" />
        </div>

        <p className="canh-trai__nhom">MENU QUẢN TRỊ</p>
        <nav className="canh-trai__menu">
          {MENU.map((muc) =>
            muc.chuaDung ? (
              <span key={muc.nhan} className="canh-trai__muc canh-trai__muc--tat">
                {muc.nhan}
                <em className="canh-trai__chua">chưa dựng</em>
              </span>
            ) : (
              <NavLink
                key={muc.nhan}
                to={muc.duongDan}
                end
                className={({ isActive }) =>
                  isActive ? 'canh-trai__muc canh-trai__muc--dang' : 'canh-trai__muc'
                }
              >
                {muc.nhan}
              </NavLink>
            ),
          )}
        </nav>

        <div className="canh-trai__chan">
          <p className="canh-trai__chan-ten">MoodBite Admin</p>
          <p className="canh-trai__chan-mo-ta">
            Trung tâm vận hành dữ liệu, giúp MoodBite luôn chính xác và đáng tin cậy.
          </p>
        </div>
      </aside>

      <div className="khu-chinh">
        <header className="thanh-tren">
          <h1 className="thanh-tren__tieu-de">{tenTrang(location.pathname)}</h1>
          <div className="thanh-tren__phai">
            <span className="thanh-tren__ai">Quản trị viên</span>
            <button className="ghost" onClick={session.logout}>
              Đăng xuất
            </button>
          </div>
        </header>

        <main className="khu-chinh__than">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
