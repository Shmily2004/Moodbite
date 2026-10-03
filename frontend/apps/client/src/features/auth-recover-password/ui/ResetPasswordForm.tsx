/**
 * VIEW: bước 2 của quên mật khẩu — đặt mật khẩu mới bằng token trong thư.
 *
 * Giống `RegisterForm`, thứ DUY NHẤT kiểm ở đây là HAI Ô MẬT KHẨU CÓ KHỚP NHAU KHÔNG:
 * backend không bao giờ thấy ô "nhập lại", nó chỉ tồn tại để chống gõ nhầm. Độ dài tối
 * thiểu và mọi luật khác vẫn do backend quyết.
 */
import { useId, useState } from 'react';
import type { ReactNode } from 'react';
import { IconEye, IconEyeOff, IconLock } from '@/shared/ui';
import { useT } from '@/shared/i18n';

export interface ResetPasswordFormProps {
  loading: boolean;
  error: string | null;
  /** Có giá trị = đã đổi xong. Khi đó form biến mất, chỉ còn lời nhắn + link đăng nhập. */
  message: string | null;
  /** `false` khi mở trang mà đường dẫn thiếu token — hỏng ngay từ đầu, đừng cho gõ. */
  hasToken: boolean;
  onSubmit: (newPassword: string) => void;
  footer?: ReactNode;
}

export function ResetPasswordForm({
  loading,
  error,
  message,
  hasToken,
  onSubmit,
  footer,
}: ResetPasswordFormProps) {
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [hienMatKhau, setHienMatKhau] = useState(false);
  // Lưu CỜ chứ không lưu câu: đổi ngôn ngữ lúc lỗi đang hiện thì câu đổi theo.
  const [loiKhop, setLoiKhop] = useState(false);
  const t = useT();

  const idMatKhau = useId();
  const idNhapLai = useId();

  return (
    <form
      className="auth-card"
      noValidate
      onSubmit={(event) => {
        event.preventDefault();
        if (password !== confirm) {
          setLoiKhop(true);
          return;
        }
        setLoiKhop(false);
        onSubmit(password);
      }}
    >
      <h1 className="auth-card__title">{t('reset.title')}</h1>

      {!hasToken ? (
        <p className="auth-card__error" role="alert">
          {t('reset.noToken')}
        </p>
      ) : message ? (
        <p className="auth-card__note" role="status">
          {message}
        </p>
      ) : (
        <>
          <p className="auth-card__sub">
            {t('reset.sub')}
          </p>

          <label className="field__label" htmlFor={idMatKhau}>
            {t('reset.newPassword')}
          </label>
          <div className="field">
            <IconLock className="field__icon" />
            <input
              id={idMatKhau}
              className="field__input"
              type={hienMatKhau ? 'text' : 'password'}
              value={password}
              placeholder={t('auth.minLength')}
              autoComplete="new-password"
              autoFocus
              required
              onChange={(event) => setPassword(event.target.value)}
            />
            <button
              type="button"
              className="field__eye"
              onClick={() => setHienMatKhau((cu) => !cu)}
              aria-label={hienMatKhau ? t('auth.hidePassword') : t('auth.showPassword')}
              aria-pressed={hienMatKhau}
              tabIndex={-1}
            >
              {hienMatKhau ? <IconEyeOff /> : <IconEye />}
            </button>
          </div>

          <label className="field__label" htmlFor={idNhapLai}>
            {t('auth.confirmPassword')}
          </label>
          <div className="field">
            <IconLock className="field__icon" />
            <input
              id={idNhapLai}
              className="field__input"
              // Cùng bật/tắt che chữ với ô trên: hai ô mà một hiện một che thì không đối
              // chiếu được, trong khi đối chiếu chính là việc của ô này.
              type={hienMatKhau ? 'text' : 'password'}
              value={confirm}
              placeholder={t('reset.confirmPlaceholder')}
              autoComplete="new-password"
              required
              onChange={(event) => setConfirm(event.target.value)}
            />
          </div>

          {(loiKhop || error) && (
            <p className="auth-card__error" role="alert">
              {loiKhop ? t('auth.mismatch') : error}
            </p>
          )}

          <button type="submit" className="btn btn--primary" disabled={loading}>
            {loading ? t('reset.submitting') : t('reset.submit')}
          </button>
        </>
      )}

      {footer && (
        <>
          <div className="auth-card__or">
            <span>{t('auth.or')}</span>
          </div>
          <p className="auth-card__footer">{footer}</p>
        </>
      )}
    </form>
  );
}
