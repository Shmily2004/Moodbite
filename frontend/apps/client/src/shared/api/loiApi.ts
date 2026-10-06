/**
 * Dịch lỗi API sang câu người dùng đọc được, THEO NGÔN NGỮ đang chọn (2026-10-06).
 *
 * Thay cho `ApiError.userMessage` — chuỗi tiếng Việt cứng trong `packages/api-client`,
 * nên bản tiếng Anh từng hiện "Không kết nối được tới server…". Package API dùng chung với
 * admin (chỉ tiếng Việt) nên giữ `userMessage` ở đó làm mặc định, còn app người dùng dịch
 * theo `code` tại đây.
 */
import { ApiError } from '@moodbite/api-client';
import type { ApiErrorCode } from '@moodbite/api-client';
import type { HamDich, Khoa } from '../i18n';

/** Mã lỗi có câu soạn sẵn. Mã khác (INVALID_REQUEST…) dùng câu backend trả về. */
const KHOA_THEO_MA: Partial<Record<ApiErrorCode, Khoa>> = {
  DATA_NOT_READY: 'apiErr.DATA_NOT_READY',
  RESTAURANT_NOT_FOUND: 'apiErr.RESTAURANT_NOT_FOUND',
  DISH_NOT_FOUND: 'apiErr.DISH_NOT_FOUND',
  EXTERNAL_SERVICE_UNAVAILABLE: 'apiErr.EXTERNAL_SERVICE_UNAVAILABLE',
  RATE_LIMITED: 'apiErr.RATE_LIMITED',
  UNAUTHORIZED: 'apiErr.UNAUTHORIZED',
  NETWORK: 'apiErr.NETWORK',
};

/**
 * Luồng TÌM QUÁN / MÓN: tương đương `userMessage` nhưng đã dịch.
 * `fallback` dùng khi không phải ApiError (lỗi lập trình) hoặc backend không gửi câu nào.
 */
export function apiErrorText(err: unknown, t: HamDich, fallback: Khoa = 'apiErr.generic'): string {
  if (err instanceof ApiError) {
    const khoa = KHOA_THEO_MA[err.code];
    if (khoa) return t(khoa);
    return err.message || t(fallback);
  }
  return t(fallback);
}

/**
 * Luồng TÀI KHOẢN / DỮ LIỆU CÁ NHÂN: ưu tiên câu backend (`message`) — nó nói đúng chuyện
 * gì sai (sai mật khẩu, tên đã có…), còn câu soạn sẵn theo mã thì nói sai hẳn (401 sai mật
 * khẩu thành "phiên hết hạn"). Riêng NETWORK thì `message` là "Failed to fetch" → dịch.
 */
export function accountErrorText(
  err: unknown,
  t: HamDich,
  fallback: Khoa = 'apiErr.generic',
): string {
  if (err instanceof ApiError) {
    if (err.code === 'NETWORK') return t('apiErr.NETWORK');
    return err.message || t(fallback);
  }
  return t(fallback);
}
