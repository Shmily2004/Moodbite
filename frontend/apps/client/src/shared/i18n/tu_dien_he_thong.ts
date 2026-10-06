/**
 * Từ điển vùng HỆ THỐNG (thêm 2026-10-06): câu lỗi API theo mã lỗi, trang lỗi khi route
 * vỡ (tải trang lười thất bại), số liệu tài khoản chưa tải được, chọn điểm trên bản đồ
 * bằng bàn phím, ghi công ảnh nền bản đồ. Gộp vào `TU_DIEN` ở `tu_dien.ts`.
 *
 * `apiErr.*` thay cho `ApiError.userMessage` (chuỗi tiếng Việt cứng trong
 * `packages/api-client`) ở app người dùng — bản tiếng Anh từng hiện câu tiếng Việt.
 * App admin chỉ có tiếng Việt nên vẫn dùng `userMessage`.
 */

export const viHeThong = {
  // --- Lỗi API theo mã (khớp `ApiErrorCode` trong packages/api-client/src/http.ts) ----
  'apiErr.DATA_NOT_READY': 'Server chưa nạp xong dữ liệu quán ăn. Hãy thử lại sau.',
  'apiErr.RESTAURANT_NOT_FOUND': 'Không tìm thấy quán này.',
  'apiErr.DISH_NOT_FOUND': 'Món này không còn trong danh mục. Hãy chọn món khác.',
  'apiErr.EXTERNAL_SERVICE_UNAVAILABLE':
    'Dịch vụ bên ngoài đang lỗi. Kết quả có thể thiếu thông tin.',
  'apiErr.RATE_LIMITED': 'Bạn thao tác hơi nhanh. Chờ một chút rồi thử lại.',
  'apiErr.UNAUTHORIZED': 'Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại.',
  'apiErr.NETWORK': 'Không kết nối được tới server. Kiểm tra mạng rồi thử lại.',
  'apiErr.generic': 'Có lỗi xảy ra.',

  // --- Trang lỗi khi route vỡ (vd. tải trang lười thất bại sau khi deploy) ------------
  'routeErr.title': 'Không mở được trang này',
  'routeErr.hint':
    'Có thể ứng dụng vừa được cập nhật hoặc mạng bị gián đoạn. Tải lại trang thường sẽ khắc phục được.',
  'routeErr.reload': 'Tải lại trang',
  'routeErr.home': 'Về trang chủ',

  // --- Ô số liệu tài khoản ----------------------------------------------------------
  'account.stat.loading': 'Đang tải số liệu',
  'account.stat.unavailable': 'Chưa có số liệu',
  'account.stat.retry': 'Thử lại',

  // --- Chọn điểm trên bản đồ không cần chuột ---------------------------------------
  'addresses.pinCenter': 'Đặt ghim ở tâm bản đồ',
  'addresses.pinCenterHint':
    'Không dùng chuột: bấm vào bản đồ rồi dùng phím mũi tên để di chuyển, sau đó bấm nút này.',

  // --- Ghi công ảnh nền bản đồ -----------------------------------------------------
  'map.basemap': 'nền',
};

export const enHeThong: Record<keyof typeof viHeThong, string> = {
  'apiErr.DATA_NOT_READY': 'The server has not finished loading restaurant data. Please try again later.',
  'apiErr.RESTAURANT_NOT_FOUND': 'This place could not be found.',
  'apiErr.DISH_NOT_FOUND': 'This dish is no longer in the catalogue. Please pick another one.',
  'apiErr.EXTERNAL_SERVICE_UNAVAILABLE':
    'An external service is down. Results may be missing some details.',
  'apiErr.RATE_LIMITED': 'You are going a bit fast. Wait a moment and try again.',
  'apiErr.UNAUTHORIZED': 'Your session has expired. Please sign in again.',
  'apiErr.NETWORK': 'Could not reach the server. Check your connection and try again.',
  'apiErr.generic': 'Something went wrong.',

  'routeErr.title': 'This page could not be opened',
  'routeErr.hint':
    'The app may have just been updated, or the network dropped. Reloading the page usually fixes it.',
  'routeErr.reload': 'Reload page',
  'routeErr.home': 'Go to home page',

  'account.stat.loading': 'Loading stats',
  'account.stat.unavailable': 'Not available yet',
  'account.stat.retry': 'Retry',

  'addresses.pinCenter': 'Drop the pin at the map centre',
  'addresses.pinCenterHint':
    'Without a mouse: focus the map, move it with the arrow keys, then press this button.',

  'map.basemap': 'basemap',
};
