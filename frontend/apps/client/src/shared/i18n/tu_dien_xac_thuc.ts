/**
 * Từ điển vùng XÁC THỰC: đăng nhập, đăng ký, quên/đặt lại mật khẩu, trang xác minh email
 * và khung `AuthLayout` (thêm 2026-10-02). Gộp vào `TU_DIEN` ở `tu_dien.ts`.
 *
 * Câu lỗi/thông báo do BACKEND trả (sai mật khẩu, đã gửi thư…) vẫn là tiếng Việt.
 */

export const viXacThuc = {
  'auth.badge': 'Made for Hà Nội!',
  'auth.or': 'hoặc',
  'auth.username': 'Tên đăng nhập',
  'auth.password': 'Mật khẩu',
  'auth.showPassword': 'Hiện mật khẩu',
  'auth.hidePassword': 'Ẩn mật khẩu',
  'auth.confirmPassword': 'Xác nhận mật khẩu',
  'auth.mismatch': 'Hai ô mật khẩu chưa giống nhau. Kiểm tra lại giúp mình nhé.',
  'auth.minLength': 'Ít nhất 8 ký tự',

  // --- Đăng nhập --------------------------------------------------------------
  'login.welcome': 'Chào mừng trở lại!',
  'login.sub': 'Đăng nhập để khám phá những món ngon phù hợp với bạn ở Hà Nội.',
  'login.usernamePlaceholder': 'Nhập tên đăng nhập',
  'login.passwordPlaceholder': 'Nhập mật khẩu',
  'login.remember': 'Ghi nhớ đăng nhập',
  'login.forgot': 'Quên mật khẩu?',
  'login.submitting': 'Đang đăng nhập…',
  'login.submit': 'Đăng nhập',
  'login.intro':
    'MoodBite gợi ý những quán ăn phù hợp với cảm xúc, thời tiết và thói quen của bạn.',
  'login.noAccount': 'Chưa có tài khoản?',
  'login.registerNow': 'Đăng ký ngay',

  // --- Đăng ký ----------------------------------------------------------------
  'register.title': 'Tạo tài khoản mới',
  'register.sub': 'Bắt đầu hành trình khám phá ẩm thực Hà Nội.',
  'register.usernamePlaceholder': 'Chọn tên đăng nhập',
  'register.usernameHint': '3–32 ký tự: chữ thường không dấu, số, dấu - và _',
  'register.displayName': 'Tên hiển thị',
  'register.displayNamePlaceholder': 'Tên hiển thị (có thể bỏ trống)',
  'register.displayNameTitle':
    'Được dùng tiếng Việt có dấu. Bỏ trống thì hiển thị theo tên đăng nhập.',
  'register.emailHint': 'Dùng để xác minh tài khoản và lấy lại mật khẩu khi bạn quên.',
  'register.emailRequired': 'Bạn cần nhập email để xác minh tài khoản và lấy lại mật khẩu.',
  'register.confirmPlaceholder': 'Nhập lại mật khẩu',
  'register.agree': 'Tôi đồng ý với',
  'register.terms': 'Điều khoản sử dụng',
  'register.termsNote':
    'Điều khoản sử dụng chưa được soạn. MoodBite là đồ án tốt nghiệp: tài khoản chỉ dùng để lưu tương tác của bạn trong phạm vi đồ án, không chia sẻ cho bên nào khác.',
  'register.submitting': 'Đang tạo tài khoản…',
  'register.submit': 'Tạo tài khoản',
  'register.haveAccount': 'Đã có tài khoản?',
  'register.loginNow': 'Đăng nhập ngay',

  // --- Quên / đặt lại mật khẩu --------------------------------------------------
  'forgot.title': 'Quên mật khẩu?',
  'forgot.sub':
    'Nhập email hoặc tên đăng nhập. Chúng mình sẽ gửi cho bạn một đường dẫn để đặt lại mật khẩu.',
  'forgot.identifier': 'Email hoặc tên đăng nhập',
  'forgot.identifierPlaceholder': 'Email hoặc tên đăng nhập của bạn',
  'forgot.sending': 'Đang gửi…',
  'forgot.submit': 'Gửi hướng dẫn đặt lại',
  'forgot.intro': 'Đừng lo, chuyện quên mật khẩu ai cũng gặp. Lấy lại chỉ mất một phút.',
  'forgot.remembered': 'Nhớ ra rồi?',
  'reset.title': 'Đặt mật khẩu mới',
  'reset.noToken':
    'Đường dẫn không hợp lệ — thiếu mã đặt lại. Hãy mở lại đúng đường dẫn trong thư, hoặc yêu cầu gửi thư mới.',
  'reset.sub':
    'Mật khẩu mới cần ít nhất 8 ký tự. Đặt xong bạn sẽ đăng nhập lại bằng mật khẩu này.',
  'reset.newPassword': 'Mật khẩu mới',
  'reset.confirmPlaceholder': 'Nhập lại mật khẩu mới',
  'reset.submitting': 'Đang đổi mật khẩu…',
  'reset.submit': 'Đổi mật khẩu',
  'reset.intro': 'Đặt mật khẩu mới xong là quay lại khám phá món ngon Hà Nội thôi.',
  'reset.done': 'Xong rồi! ',
  'reset.changedMind': 'Đổi ý? ',
  'reset.toLogin': 'Về trang đăng nhập',

  // --- Trang xác minh email -----------------------------------------------------
  'verifyPage.intro': 'Xác minh xong là bạn lấy lại được mật khẩu qua email khi cần.',
  'verifyPage.noToken': 'Đường dẫn thiếu mã xác minh. Hãy mở lại đúng đường dẫn trong thư.',
  'verifyPage.redirect': 'Đang đưa bạn về trang chủ sau {n} giây…',
  'verifyPage.goNow': 'Về ngay',
  'verifyPage.home': 'Về trang chủ',
  'verifyPage.account': 'Trang tài khoản',
} as const;

export const enXacThuc: Record<keyof typeof viXacThuc, string> = {
  'auth.badge': 'Made for Hanoi!',
  'auth.or': 'or',
  'auth.username': 'Username',
  'auth.password': 'Password',
  'auth.showPassword': 'Show password',
  'auth.hidePassword': 'Hide password',
  'auth.confirmPassword': 'Confirm password',
  'auth.mismatch': "The two passwords don't match. Please check again.",
  'auth.minLength': 'At least 8 characters',

  'login.welcome': 'Welcome back!',
  'login.sub': 'Sign in to discover tasty dishes in Hanoi that suit you.',
  'login.usernamePlaceholder': 'Enter your username',
  'login.passwordPlaceholder': 'Enter your password',
  'login.remember': 'Remember me',
  'login.forgot': 'Forgot password?',
  'login.submitting': 'Signing in…',
  'login.submit': 'Sign in',
  'login.intro': 'MoodBite suggests places to eat that match your mood, the weather and your habits.',
  'login.noAccount': "Don't have an account?",
  'login.registerNow': 'Sign up now',

  'register.title': 'Create a new account',
  'register.sub': "Start exploring Hanoi's food.",
  'register.usernamePlaceholder': 'Choose a username',
  'register.usernameHint': '3–32 characters: lowercase letters without accents, digits, - and _',
  'register.displayName': 'Display name',
  'register.displayNamePlaceholder': 'Display name (optional)',
  'register.displayNameTitle':
    'Vietnamese with accents is allowed. Leave it empty to show your username.',
  'register.emailHint': 'Used to verify your account and to reset your password if you forget it.',
  'register.emailRequired': 'Please enter an email to verify your account and reset your password.',
  'register.confirmPlaceholder': 'Re-enter your password',
  'register.agree': 'I agree to the',
  'register.terms': 'Terms of use',
  'register.termsNote':
    'The terms of use have not been written yet. MoodBite is a graduation project: your account only stores your interactions within the project and is never shared with anyone else.',
  'register.submitting': 'Creating account…',
  'register.submit': 'Create account',
  'register.haveAccount': 'Already have an account?',
  'register.loginNow': 'Sign in now',

  'forgot.title': 'Forgot password?',
  'forgot.sub': "Enter your email or username. We'll send you a link to reset your password.",
  'forgot.identifier': 'Email or username',
  'forgot.identifierPlaceholder': 'Your email or username',
  'forgot.sending': 'Sending…',
  'forgot.submit': 'Send reset instructions',
  'forgot.intro': "Don't worry, everyone forgets a password. Getting it back takes a minute.",
  'forgot.remembered': 'Remembered it?',
  'reset.title': 'Set a new password',
  'reset.noToken':
    'Invalid link — the reset code is missing. Open the exact link from the email again, or request a new email.',
  'reset.sub':
    "Your new password needs at least 8 characters. You'll sign in again with it afterwards.",
  'reset.newPassword': 'New password',
  'reset.confirmPlaceholder': 'Re-enter the new password',
  'reset.submitting': 'Changing password…',
  'reset.submit': 'Change password',
  'reset.intro': 'Set a new password and get back to exploring Hanoi food.',
  'reset.done': 'All done! ',
  'reset.changedMind': 'Changed your mind? ',
  'reset.toLogin': 'Back to sign in',

  'verifyPage.intro': 'Once verified, you can reset your password by email whenever needed.',
  'verifyPage.noToken': 'The link is missing its verification code. Open the exact link from the email again.',
  'verifyPage.redirect': 'Taking you to the home page in {n} seconds…',
  'verifyPage.goNow': 'Go now',
  'verifyPage.home': 'Home page',
  'verifyPage.account': 'Account page',
};
