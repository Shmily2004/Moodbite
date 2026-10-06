/**
 * Báo "phiên quản trị đã chết" từ tầng gọi API lên `features/admin-login`.
 *
 * VÌ SAO (audit 2026-10-06): trước đây chỉ trang Quán tự bắt 401 và gọi `handleExpired`;
 * các trang khác (Tổng quan, Món, Chất lượng, Cần xử lý…) kẹt ở thông báo lỗi khi token
 * hết hạn (1 giờ) hoặc bị thu hồi. Nay `adminApi` gọi `handleUnauthorized` cho MỌI 401 có
 * token, `useAdminSession` lắng nghe và đưa về trang đăng nhập — một chỗ cho mọi trang.
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

/** Chỉ xử lý khi token gây 401 VẪN là token hiện tại — 401 của request cũ thì bỏ qua. */
export function handleUnauthorized(sentToken: string): void {
  if (readToken() !== sentToken) return;
  clearToken();
  listeners.forEach((listener) => listener());
}
