/**
 * Từ điển vùng TÀI KHOẢN: thẻ đầu trang, ảnh đại diện, đổi mật khẩu, sở thích, xác minh
 * email, bảng điểm, và câu lỗi dự phòng của các hook dữ liệu cá nhân (thêm 2026-10-02).
 * Gộp vào `TU_DIEN` ở `tu_dien.ts`.
 *
 * Câu lỗi do BACKEND trả về vẫn là tiếng Việt (backend chưa có i18n) — ở đây chỉ dịch
 * câu DỰ PHÒNG khi không có câu nào từ server.
 */

export const viTaiKhoan = {
  'account.verified': '✓ đã xác minh',
  'account.unverified': 'chưa xác minh',

  // Bảng điểm — mỗi con số phải khớp `domain/services/gamification.py`.
  'points.viewPlace': 'Xem chi tiết một quán mới',
  'points.directions': 'Bấm chỉ đường tới một quán',
  'points.feedback': 'Đánh giá thích / không thích',
  'points.save': 'Lưu một món hoặc một quán',
  'points.report': 'Báo một quán đã đóng cửa',
  'points.note1': 'Điểm tính theo số ',
  'points.note2': 'quán/món khác nhau',
  'points.note3':
    ', không theo số lần bấm — xem lại cùng một quán hai chục lần vẫn chỉ được tính một.',

  // --- Ảnh đại diện -----------------------------------------------------------
  'avatar.hint':
    'PNG, JPG hoặc WEBP, tối đa 2 MB. Ảnh chỉ lưu trên máy bạn, không gửi lên máy chủ.',
  'avatar.processing': 'Đang xử lý…',
  'avatar.change': 'Đổi ảnh đại diện',
  'avatar.upload': 'Tải ảnh đại diện lên',
  'avatar.useDefault': 'Dùng ảnh mặc định',
  'avatar.err.generic': 'Không xử lý được ảnh này.',
  'avatar.err.read': 'Không đọc được file.',
  'avatar.err.canvas': 'Trình duyệt không vẽ lại được ảnh.',
  'avatar.err.process': 'Không xử lý được ảnh.',
  'avatar.err.decode': 'File này không phải ảnh hợp lệ.',
  'avatar.err.tooBig': 'Ảnh lớn quá ({mb} MB). Tối đa 2 MB.',
  'avatar.err.type': 'Chỉ nhận ảnh PNG, JPG hoặc WEBP.',
  'avatar.err.fake': 'File này không phải ảnh thật. Hãy chọn ảnh khác.',

  // --- Đổi mật khẩu ---------------------------------------------------------
  'changePw.failed': 'Không đổi được mật khẩu.',
  'changePw.current': 'Mật khẩu hiện tại',
  'changePw.new': 'Mật khẩu mới',
  'changePw.sending': 'Đang đổi…',
  'changePw.submit': 'Đổi mật khẩu',

  // --- Ô sở thích (features/taste-preferences, khoá theo `SoThich.id`) -------
  'taste.opt.nuong': 'Đồ nướng',
  'taste.opt.nuoc': 'Món nước',
  'taste.opt.chien': 'Chiên rán',
  'taste.opt.hap': 'Hấp / luộc',
  'taste.opt.tron': 'Món trộn',
  'taste.opt.nong': 'Món nóng',
  'taste.opt.mat': 'Đồ mát',
  'taste.opt.cay': 'Ăn cay',

  // --- Xác minh email ---------------------------------------------------------
  'verify.title': 'Xác minh email',
  'verify.running': 'Đang xác minh…',
  'verify.noEmail': 'Chưa khai email — thêm email để lấy lại mật khẩu khi cần.',
  'verify.verified': '✓ Email đã xác minh',
  'verify.unverified': 'Email chưa xác minh',
  'verify.sending': 'Đang gửi…',
  'verify.resend': 'Gửi lại thư xác minh',
  'verify.done': 'Đã xác minh email. Từ giờ bạn lấy lại được mật khẩu qua email.',

  // --- Lặt vặt -----------------------------------------------------------------
  'theme.toLight': 'Chuyển sang nền sáng',
  'theme.toDark': 'Chuyển sang nền tối',
  'home.recentSub':
    'Món bạn vừa mở trên máy này. Lưu ngay trong trình duyệt, không gửi lên máy chủ.',

  // --- Câu lỗi dự phòng của các hook ------------------------------------------
  'err.stats': 'Không tải được số liệu.',
  'err.favLoad': 'Không tải được danh sách đã lưu.',
  'err.favSave': 'Không lưu được. Thử lại nhé.',
  'err.addrLoad': 'Không tải được địa chỉ.',
  'err.addrSave': 'Không lưu được địa chỉ.',
  'err.addrDefault': 'Không đổi được mặc định.',
  'err.addrDelete': 'Không xoá được địa chỉ.',
  'err.colLoad': 'Không tải được bộ sưu tập.',
  'err.colCreate': 'Không tạo được bộ sưu tập.',
  'err.colRename': 'Không đổi được tên.',
  'err.colDelete': 'Không xoá được bộ sưu tập.',
  'err.colAdd': 'Không thêm được vào bộ.',
  'err.colRemove': 'Không bỏ được mục khỏi bộ.',
} as const;

export const enTaiKhoan: Record<keyof typeof viTaiKhoan, string> = {
  'account.verified': '✓ verified',
  'account.unverified': 'not verified',

  'points.viewPlace': 'Open the details of a new place',
  'points.directions': 'Get directions to a place',
  'points.feedback': 'Like / dislike a place',
  'points.save': 'Save a dish or a place',
  'points.report': 'Report a place as closed',
  'points.note1': 'Points count ',
  'points.note2': 'distinct places/dishes',
  'points.note3':
    ', not clicks — viewing the same place twenty times still counts once.',

  'avatar.hint':
    'PNG, JPG or WEBP, up to 2 MB. The picture stays on this device and is never uploaded.',
  'avatar.processing': 'Processing…',
  'avatar.change': 'Change profile picture',
  'avatar.upload': 'Upload a profile picture',
  'avatar.useDefault': 'Use the default picture',
  'avatar.err.generic': 'Could not process this picture.',
  'avatar.err.read': 'Could not read the file.',
  'avatar.err.canvas': 'The browser could not redraw the picture.',
  'avatar.err.process': 'Could not process the picture.',
  'avatar.err.decode': 'This file is not a valid image.',
  'avatar.err.tooBig': 'The picture is too large ({mb} MB). Maximum 2 MB.',
  'avatar.err.type': 'Only PNG, JPG or WEBP images are accepted.',
  'avatar.err.fake': 'This file is not a real image. Please pick another one.',

  'changePw.failed': 'Could not change the password.',
  'changePw.current': 'Current password',
  'changePw.new': 'New password',
  'changePw.sending': 'Changing…',
  'changePw.submit': 'Change password',

  'taste.opt.nuong': 'Grilled',
  'taste.opt.nuoc': 'Noodle soup',
  'taste.opt.chien': 'Fried',
  'taste.opt.hap': 'Steamed / boiled',
  'taste.opt.tron': 'Tossed salads',
  'taste.opt.nong': 'Hot dishes',
  'taste.opt.mat': 'Cool dishes',
  'taste.opt.cay': 'Spicy',

  'verify.title': 'Verify your email',
  'verify.running': 'Verifying…',
  'verify.noEmail': 'No email yet — add one so you can reset your password if needed.',
  'verify.verified': '✓ Email verified',
  'verify.unverified': 'Email not verified',
  'verify.sending': 'Sending…',
  'verify.resend': 'Resend verification email',
  'verify.done': 'Email verified. You can now reset your password by email.',

  'theme.toLight': 'Switch to light theme',
  'theme.toDark': 'Switch to dark theme',
  'home.recentSub':
    'Dishes you just opened on this device. Stored in your browser only, never sent to the server.',

  'err.stats': 'Could not load your stats.',
  'err.favLoad': 'Could not load your saved list.',
  'err.favSave': 'Could not save. Please try again.',
  'err.addrLoad': 'Could not load your addresses.',
  'err.addrSave': 'Could not save the address.',
  'err.addrDefault': 'Could not change the default.',
  'err.addrDelete': 'Could not delete the address.',
  'err.colLoad': 'Could not load your collections.',
  'err.colCreate': 'Could not create the collection.',
  'err.colRename': 'Could not rename it.',
  'err.colDelete': 'Could not delete the collection.',
  'err.colAdd': 'Could not add it to the collection.',
  'err.colRemove': 'Could not remove the item from the collection.',
};
