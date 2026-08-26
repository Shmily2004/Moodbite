/**
 * Trang XÁC MINH EMAIL — mở từ đường dẫn trong thư.
 *
 * Token nằm ở query string `?token=...`. Đọc bằng `useSearchParams` của react-router chứ
 * không tự cắt chuỗi từ `window.location`: token là chuỗi base64url có thể chứa ký tự
 * cần mã hoá URL — đúng lý do đã ghi ở `ResetPasswordPage`.
 *
 * XÁC MINH XONG THÌ TỰ VỀ TRANG CHỦ (chủ dự án chốt 2026-08-26).
 * Trước đó trang chỉ hiện một dòng chữ rồi đứng im, người dùng bấm link trong thư xong
 * "không thấy gì hiện lên" và không biết đã xong hay chưa.
 *
 * VÌ SAO ĐỢI VÀI GIÂY CHỨ KHÔNG NHẢY NGAY: nhảy ngay thì người dùng không kịp đọc là
 * việc đã thành công — họ chỉ thấy trang chủ và vẫn không biết email đã xác minh chưa.
 * Đợi có ĐẾM NGƯỢC nhìn thấy được, kèm nút đi ngay cho ai không muốn chờ.
 *
 * ⚠️ CHỈ tự chuyển khi THÀNH CÔNG. Lỗi thì phải ở lại để người dùng đọc được câu lỗi và
 * bấm gửi lại thư — đá họ về trang chủ lúc đó là giấu mất lỗi.
 */
import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { AuthLayout } from '@/widgets/auth-layout';
import { EmailVerificationStatus, useEmailVerification } from '@/features/auth-verify-email';
import { Slogan } from '@/shared/ui';
import { ROUTES } from '@/shared/config';

/** Đủ để đọc xong câu "đã xác minh" mà không thành ngồi đợi. */
const GIAY_DEM_NGUOC = 3;

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') ?? '';
  const xacMinh = useEmailVerification(token);
  const xong = xacMinh.status === 'done';

  const [conLai, setConLai] = useState(GIAY_DEM_NGUOC);

  useEffect(() => {
    if (!xong) return;

    const dem = setInterval(() => setConLai((n) => n - 1), 1000);
    // `replace: true` để bấm Back KHÔNG quay lại đây: token đã dùng rồi, quay lại chỉ
    // gặp "đường dẫn không còn hiệu lực" — trông hệt như một lỗi.
    const di = setTimeout(
      () => navigate(ROUTES.home, { replace: true }),
      GIAY_DEM_NGUOC * 1000,
    );

    return () => {
      clearInterval(dem);
      clearTimeout(di);
    };
  }, [xong, navigate]);

  return (
    <AuthLayout
      heading={<Slogan />}
      intro="Xác minh xong là bạn lấy lại được mật khẩu qua email khi cần."
    >
      <EmailVerificationStatus
        status={xacMinh.status}
        message={xacMinh.message}
        // Mở trang thẳng (không qua thư) thì nói rõ, đừng để trang trắng.
        error={
          token === ''
            ? 'Đường dẫn thiếu mã xác minh. Hãy mở lại đúng đường dẫn trong thư.'
            : xacMinh.error
        }
        verified={xong}
        hasEmail
        variant="page"
        footer={
          xong ? (
            <>
              <span role="status">
                Đang đưa bạn về trang chủ sau {Math.max(0, conLai)} giây…
              </span>{' '}
              <Link to={ROUTES.home} replace>
                Về ngay
              </Link>
            </>
          ) : (
            <>
              <Link to={ROUTES.home}>Về trang chủ</Link>
              {' · '}
              <Link to={ROUTES.account}>Trang tài khoản</Link>
            </>
          )
        }
      />
    </AuthLayout>
  );
}
