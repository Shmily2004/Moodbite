/**
 * Đường dẫn của app quản trị, khai ở MỘT chỗ duy nhất.
 *
 * VÌ SAO Ở `shared/` CHỨ KHÔNG Ở `app/`: cả `app/` (đăng ký route, chuyển hướng) lẫn
 * `pages/` (link qua lại) đều cần. Luật FSD chỉ cho import đi XUỐNG, nên nếu để ở
 * `app/` thì `pages/` sẽ phải import ngược lên — `steiger` chặn ngay.
 *
 * Đặt ở đây rồi thì đổi đường dẫn chỉ sửa một chỗ, không phải đi tìm chuỗi '/login'
 * rải rác trong code.
 */
export const ROUTES = {
  // Khu quản trị nằm dưới `/quan-tri` của app người dùng (gộp 2026-11-01): một trang đăng
  // nhập, một phiên. Đăng nhập CHUNG ở `/login` của app người dùng — không còn trang riêng.
  login: '/login',
  // Trang chủ khu quản trị = TỔNG QUAN (đổi 2026-08-26 theo `design/Dashboard admin.png`).
  // Trước đó `/` là danh sách quán; đăng nhập xong đập ngay vào một bảng 52.854 dòng.
  overview: '/quan-tri',
  restaurants: '/quan-tri/quan-an',
  dishes: '/quan-tri/mon-an',
  // Trang chi tiết món là ROUTE THẬT (2026-09-16), thay cho ô trượt bên cạnh bảng: có
  // đường dẫn riêng thì gửi link cho nhau được, và nút Back của trình duyệt quay về đúng
  // bảng đang lọc.
  dishDetail: '/quan-tri/mon-an/:dishId',
  quality: '/quan-tri/chat-luong',
  issues: '/quan-tri/can-xu-ly',
  recommendation: '/quan-tri/goi-y',
  activity: '/quan-tri/nhat-ky',
  system: '/quan-tri/cai-dat',
} as const;

/**
 * "Cần xử lý" ở trang Tổng quan bấm sang đâu.
 *
 * Khoá là `key` do BACKEND đặt (`domain/services/data_quality.py`). Khoá nào không có ở
 * đây thì dòng đó KHÔNG bấm được — cố ý: thà không bấm được còn hơn dẫn tới một danh
 * sách không lọc đúng thứ vừa hứa.
 */
export const DUONG_DAN_CAN_XU_LY: Record<string, string> = {
  dong_tam: `${ROUTES.restaurants}?loc=dong_tam`,
  thieu_lien_he: `${ROUTES.restaurants}?loc=thieu_lien_he`,
  mon_thieu_anh: `${ROUTES.dishes}?filter=missing_image`,
  mon_thieu_mo_ta: `${ROUTES.dishes}?filter=missing_description`,
  mon_khong_quan: `${ROUTES.dishes}?filter=without_restaurants`,
};

/** Đường dẫn trang chi tiết một món. Mã món được mã hoá để ký tự lạ không làm gãy URL. */
export function duongDanMon(dishId: string): string {
  return `${ROUTES.dishes}/${encodeURIComponent(dishId)}`;
}
