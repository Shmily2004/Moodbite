/**
 * Lưu token đăng nhập của admin.
 *
 * Dùng `sessionStorage` chứ KHÔNG dùng `localStorage`: token hết hiệu lực sau 1 giờ, và
 * sessionStorage tự xoá khi đóng tab. Trên máy dùng chung, `localStorage` giữ token lại
 * cho người mở trình duyệt tiếp theo — rủi ro không cần thiết đổi lấy tiện lợi rất nhỏ.
 */
const KEY = 'moodbite.admin.token';

export function readToken(): string | null {
  try {
    return sessionStorage.getItem(KEY);
  } catch {
    // Trình duyệt chặn storage (chế độ riêng tư) -> coi như chưa đăng nhập, không nổ.
    return null;
  }
}

export function writeToken(token: string): void {
  try {
    sessionStorage.setItem(KEY, token);
  } catch {
    /* không lưu được thì phiên chỉ sống trong bộ nhớ - vẫn dùng được */
  }
}

export function clearToken(): void {
  try {
    sessionStorage.removeItem(KEY);
  } catch {
    /* bỏ qua */
  }
}
