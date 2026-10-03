/** VIEW: bước 1 của quên mật khẩu — gõ email hoặc tên đăng nhập để nhận thư. */
import { useId, useState } from 'react';
import type { ReactNode } from 'react';
import { IconUser } from '@/shared/ui';
import { useT } from '@/shared/i18n';

export interface ForgotPasswordFormProps {
  loading: boolean;
  error: string | null;
  /** Câu backend trả về khi đã nhận yêu cầu. Có giá trị nghĩa là đã gửi xong. */
  message: string | null;
  onSubmit: (identifier: string) => void;
  footer?: ReactNode;
}

export function ForgotPasswordForm({
  loading,
  error,
  message,
  onSubmit,
  footer,
}: ForgotPasswordFormProps) {
  const [identifier, setIdentifier] = useState('');
  const idOTim = useId();
  const t = useT();

  return (
    <form
      className="auth-card"
      noValidate
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(identifier);
      }}
    >
      <h1 className="auth-card__title">{t('forgot.title')}</h1>
      <p className="auth-card__sub">
        {t('forgot.sub')}
      </p>

      {message ? (
        /*
          Đã gửi xong thì ẨN HẲN ô nhập, chỉ còn lời nhắn.

          Vì sao không để ô nhập lại đó: người dùng không thấy phản hồi rõ ràng sẽ bấm gửi
          thêm vài lần nữa, mà mỗi lần là một lá thư thật và backend chỉ cho 3 lần/giờ.
        */
        <p className="auth-card__note" role="status">
          {message}
        </p>
      ) : (
        <>
          <label className="field__label" htmlFor={idOTim}>
            {t('forgot.identifier')}
          </label>
          <div className="field">
            <IconUser className="field__icon" />
            <input
              id={idOTim}
              className="field__input"
              value={identifier}
              placeholder={t('forgot.identifierPlaceholder')}
              autoComplete="username"
              autoFocus
              required
              onChange={(event) => setIdentifier(event.target.value)}
            />
          </div>

          {error && (
            <p className="auth-card__error" role="alert">
              {error}
            </p>
          )}

          <button type="submit" className="btn btn--primary" disabled={loading}>
            {loading ? t('forgot.sending') : t('forgot.submit')}
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
