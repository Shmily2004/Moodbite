/**
 * Trang đăng ký — tầng `pages`: chỉ NỐI khung (`AuthLayout`), VIEW (`RegisterForm`) và
 * VIEWMODEL (`useUserSessionContext`) lại với nhau. Không có logic riêng.
 *
 * Dùng LẠI đúng khung của trang đăng nhập, chỉ đổi tranh nền — như bản thiết kế. Nhờ vậy
 * sửa thanh trên (logo, ngôn ngữ, nút nền tối) là cả hai trang cùng đổi, không có chuyện
 * hai trang lệch nhau vì quên sửa một chỗ.
 */
import { Link, Navigate } from 'react-router-dom';
import { AuthLayout } from '@/widgets/auth-layout';
import { RegisterForm } from '@/features/auth-register';
import { useUserSessionContext } from '@/entities/user';
import { ROUTES } from '@/shared/config';

export function RegisterPage() {
  const session = useUserSessionContext();

  if (session.isLoggedIn) {
    // Đăng ký thành công (hoặc mở /dang-ky khi đã đăng nhập) -> vào thẳng app.
    // Backend trả token ngay lúc tạo tài khoản nên không phải đăng nhập lại lần nữa.
    return <Navigate to={ROUTES.home} replace />;
  }

  return (
    <AuthLayout scene="nen_dang_ky">
      <RegisterForm
        loading={session.loading}
        error={session.error}
        onSubmit={(username, password, displayName) =>
          void session.register(username, password, displayName)
        }
        footer={
          <>
            Đã có tài khoản? <Link to={ROUTES.login}>Đăng nhập ngay</Link>
          </>
        }
      />
    </AuthLayout>
  );
}
