/**
 * Báo "phiên đăng nhập đã chết" từ tầng gọi API lên tầng phiên người dùng.
 *
 * VÌ SAO CÓ: server THU HỒI token ở MỌI thiết bị khi đăng xuất / đổi mật khẩu. Trước
 * 2026-10-06 app chỉ phát hiện điều đó ở `/auth/me` lúc mở trang → giữa phiên, mọi lời
 * gọi `/me/*` cứ 401 mà giao diện vẫn tưởng đang đăng nhập.
 *
 * `shared/api` gọi `handleUnauthorized` (qua `onUnauthorized` của HttpClient);
 * `entities/user` lắng nghe bằng `onSessionExpired`. Đi qua `shared` để giữ luật import
 * FSD: `shared` không được import ngược lên `entities`.
 */
import { clearToken, readToken } from './tokenStorage';

type Listener = () => void;
const listeners = new Set<Listener>();

export function onSessionExpired(listener: Listener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/**
 * Một request ĐÃ GỬI `sentToken` vừa nhận 401.
 *
 * Chỉ đăng xuất khi token đó VẪN là token hiện tại: 401 của request cũ (người dùng đã
 * đăng nhập lại, hoặc chính lệnh đăng xuất vừa xoá token) thì bỏ qua — không lặp, không
 * đá văng phiên mới.
 */
export function handleUnauthorized(sentToken: string): void {
  if (readToken() !== sentToken) return;
  clearToken();
  listeners.forEach((listener) => listener());
}
