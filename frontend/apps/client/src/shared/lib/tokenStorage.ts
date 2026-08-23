/**
 * Lưu token đăng nhập của NGƯỜI DÙNG CUỐI.
 *
 * KHÁC với admin (`apps/admin` luôn dùng sessionStorage): ở đây chính người dùng chọn,
 * qua ô "Ghi nhớ đăng nhập" trong form.
 *
 *   - Có tick  -> `localStorage`: đóng trình duyệt mở lại vẫn còn. Token sống 24 giờ
 *                 (backend đặt), nên rủi ro có chặn trên rõ ràng.
 *   - Không tick -> `sessionStorage`: đóng tab là mất. Đây là lựa chọn đúng cho máy
 *                 dùng chung (máy trường, quán net).
 *
 * VÌ SAO KHÔNG DÙNG COOKIE HttpOnly — vốn an toàn hơn trước XSS: backend hiện ký token
 * HMAC stateless và trả trong body (`/auth/login`), không set cookie. Đổi sang cookie
 * là đổi HỢP ĐỒNG API + cần chống CSRF, phải chốt trước chứ không tự làm.
 */
const KEY = 'moodbite.user.token';

/** Đọc token ở CẢ HAI kho. Phiên tạm được ưu tiên: nó là lần đăng nhập gần nhất. */
export function readToken(): string | null {
  try {
    return sessionStorage.getItem(KEY) ?? localStorage.getItem(KEY);
  } catch {
    // Trình duyệt chặn storage (chế độ riêng tư) -> coi như chưa đăng nhập, không nổ.
    return null;
  }
}

/**
 * Ghi token. `remember = true` thì giữ qua các lần mở trình duyệt.
 *
 * Luôn XOÁ ở kho kia trước khi ghi: người dùng đổi ý giữa hai lần đăng nhập mà còn sót
 * token cũ ở localStorage thì "không ghi nhớ" hoá ra vẫn nhớ — đúng kiểu lỗi âm thầm.
 */
export function writeToken(token: string, remember: boolean): void {
  try {
    localStorage.removeItem(KEY);
    sessionStorage.removeItem(KEY);
    const store = remember ? localStorage : sessionStorage;
    store.setItem(KEY, token);
  } catch {
    /* không lưu được thì phiên chỉ sống trong bộ nhớ - vẫn dùng được */
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(KEY);
    sessionStorage.removeItem(KEY);
  } catch {
    /* bỏ qua */
  }
}
