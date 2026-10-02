/**
 * LAYOUT của app quản trị — khung dùng chung cho mọi trang SAU KHI đăng nhập.
 *
 * Dựng theo `frontend/design/Dashboard admin.png` (chủ dự án gửi 2026-08-26):
 * CỘT TRÁI cố định (logo + menu có biểu tượng) và thanh trên (breadcrumb + tài khoản).
 *
 * Bổ sung 2026-09-16:
 *   - Biểu tượng SVG nội tuyến cho từng mục menu (không emoji — xem `shared/ui/Icon.tsx`).
 *   - Breadcrumb trên thanh đầu: "Quản lý món ăn › Bún chả". Nhãn cuối do trang con đặt
 *     qua `useDatNhanBreadcrumb` (chỉ trang chi tiết mới biết tên món).
 *   - Dòng "Phiên bản x.y.z" đọc từ `apps/admin/package.json`, không gõ tay.
 *   - BANNER "DỮ LIỆU GIẢ LẬP" khi `GET /admin/system` trả `synthetic_data === true`.
 *
 * ⚠️ HAI THỨ TRONG BẢN THIẾT KẾ CỐ TÌNH KHÔNG DỰNG:
 *   - Ô "Tìm kiếm nhanh… Ctrl K": backend không có endpoint tìm chung quán + món + vấn đề.
 *     Mỗi trang đã có ô tìm riêng; một ô tìm ở thanh đầu không tìm được gì là nói dối.
 *   - Chuông thông báo (số 12): không có nguồn thông báo nào. Số việc cần xử lý đã nằm ở
 *     menu "Cần xử lý" và trang Tổng quan.
 *
 * Cơ chế `chuaDung` (hiện mờ, không bấm được) VẪN GIỮ LẠI dù hiện không mục nào dùng:
 * nó là cách đúng để thêm một mục đã có bản vẽ nhưng chưa có trang.
 */
import { NavLink, Outlet, useLocation, Link } from 'react-router-dom';
import { useAdminSessionContext } from '@/features/admin-login';
import { useSystem } from '@/features/view-system';
import { APP_VERSION, ROUTES } from '@/shared/config';
import { BreadcrumbProvider, useNhanBreadcrumb } from '@/shared/lib';
import { Icon, type TenIcon } from '@/shared/ui';

interface MucMenu {
  duongDan: string;
  nhan: string;
  icon: TenIcon;
  /** Chưa dựng -> hiện mờ, không bấm được. */
  chuaDung?: boolean;
}

/** Thứ tự đúng như bản thiết kế. */
const MENU: MucMenu[] = [
  { duongDan: ROUTES.overview, nhan: 'Tổng quan', icon: 'tong-quan' },
  { duongDan: ROUTES.dishes, nhan: 'Quản lý món ăn', icon: 'mon-an' },
  { duongDan: ROUTES.restaurants, nhan: 'Quản lý quán ăn', icon: 'quan-an' },
  { duongDan: ROUTES.quality, nhan: 'Chất lượng dữ liệu', icon: 'chat-luong' },
  { duongDan: ROUTES.issues, nhan: 'Cần xử lý', icon: 'can-xu-ly' },
  { duongDan: ROUTES.recommendation, nhan: 'Gợi ý & Hệ thống', icon: 'goi-y' },
  { duongDan: ROUTES.activity, nhan: 'Nhật ký hoạt động', icon: 'nhat-ky' },
  { duongDan: ROUTES.system, nhan: 'Cài đặt hệ thống', icon: 'cai-dat' },
];

/**
 * Mục menu chứa đường dẫn hiện tại. Khớp cả TRANG CON (`/mon-an/bun-cha` thuộc "Quản lý
 * món ăn"), chọn tiền tố DÀI NHẤT; `/` chỉ khớp đúng `/`, nếu không mọi trang đều thuộc
 * "Tổng quan".
 */
function mucHienTai(duongDan: string): MucMenu | null {
  const ung = MENU.filter(
    (m) =>
      !m.chuaDung &&
      (m.duongDan === duongDan ||
        (m.duongDan !== '/' && duongDan.startsWith(`${m.duongDan}/`))),
  );
  return ung.sort((a, b) => b.duongDan.length - a.duongDan.length)[0] ?? null;
}

export function AdminLayout() {
  return (
    <BreadcrumbProvider>
      <Khung />
    </BreadcrumbProvider>
  );
}

function Khung() {
  const session = useAdminSessionContext();
  const location = useLocation();
  const muc = mucHienTai(location.pathname);
  const laTrangCon = muc != null && muc.duongDan !== location.pathname;
  const nhanCuoi = useNhanBreadcrumb();
  const { data: heThong } = useSystem();
  // Trường có thể CHƯA có ở backend cũ -> coi như false. Chỉ `=== true` mới hiện banner:
  // hiện nhầm banner giả lập trên dữ liệu thật cũng sai y như giấu nó đi.
  const gia = (heThong as { synthetic_data?: boolean } | null)?.synthetic_data === true;
  const soKhoLoi = heThong ? heThong.services.filter((s) => !s.ready).length : null;

  return (
    <div className="quan-tri">
      <aside className="canh-trai">
        <div className="canh-trai__hieu">
          <img src="/anh/logo.png" alt="MoodBite" className="canh-trai__logo" />
        </div>

        <p className="canh-trai__nhom">MENU QUẢN TRỊ</p>
        <nav className="canh-trai__menu">
          {MENU.map((m) =>
            m.chuaDung ? (
              <span key={m.nhan} className="canh-trai__muc canh-trai__muc--tat">
                <span className="canh-trai__trai">
                  <Icon ten={m.icon} />
                  {m.nhan}
                </span>
                <em className="canh-trai__chua">chưa dựng</em>
              </span>
            ) : (
              <NavLink
                key={m.nhan}
                to={m.duongDan}
                // `end` CHỈ cho Tổng quan: mục khác phải còn sáng khi đang ở trang con
                // (`/mon-an/bun-cha` vẫn thuộc "Quản lý món ăn").
                end={m.duongDan === ROUTES.overview}
                className={({ isActive }) =>
                  isActive ? 'canh-trai__muc canh-trai__muc--dang' : 'canh-trai__muc'
                }
              >
                <span className="canh-trai__trai">
                  <Icon ten={m.icon} />
                  {m.nhan}
                </span>
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
        <div className="canh-trai__phien-ban small muted">
          <p>Phiên bản {APP_VERSION}</p>
          {/* Trạng thái lấy từ `/admin/system` thật; chưa tải được thì im lặng, KHÔNG
              mặc định "hoạt động tốt". */}
          {soKhoLoi != null && (
            <p>
              <span className={soKhoLoi === 0 ? 'cham cham--tot' : 'cham cham--thieu'} />
              {soKhoLoi === 0
                ? 'Mọi kho dữ liệu sẵn sàng'
                : `${soKhoLoi} kho dữ liệu chưa sẵn sàng`}
            </p>
          )}
        </div>
      </aside>

      <div className="khu-chinh">
        {gia && (
          <div className="banner-gia-lap" role="alert">
            <Icon ten="canh-bao" />
            <strong>DỮ LIỆU GIẢ LẬP</strong> — số liệu không phải người dùng thật
          </div>
        )}
        <header className="thanh-tren">
          <div className="thanh-tren__trai">
            {/* Breadcrumb CHỈ ở trang con. Ở trang cấp một nó chỉ lặp lại đúng tiêu đề
                ngay bên dưới, thêm nhiễu mà không thêm thông tin.
                Ở trang con thì NGƯỢC LẠI: breadcrumb đã nói "Quản lý món ăn › Bún chả",
                tiêu đề lặp lại "Quản lý món ăn" ngay dưới là thừa — bản thiết kế chỉ có
                breadcrumb. Tiêu đề vẫn giữ cho trình đọc màn hình (`sr-only`). */}
            {laTrangCon && muc && (
              <nav aria-label="Breadcrumb" className="duong-dan duong-dan--chinh">
                <ol>
                  <li>
                    <Link to={muc.duongDan}>{muc.nhan}</Link>
                  </li>
                  <li aria-current="page">{nhanCuoi ?? 'Chi tiết'}</li>
                </ol>
              </nav>
            )}
            <h1 className={laTrangCon && muc ? 'sr-only' : 'thanh-tren__tieu-de'}>
              {muc?.nhan ?? 'Quản trị'}
            </h1>
          </div>
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
