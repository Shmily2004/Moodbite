/** VIEW: bước 1 của quên mật khẩu — gõ email hoặc tên đăng nhập để nhận thư. */
import { useId, useState } from 'react';
import type { ReactNode } from 'react';
import { IconUser } from '@/shared/ui';

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

  return (
    <form
      className="auth-card"
      noValidate
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(identifier);
      }}
    >
      <h1 className="auth-card__title">Quên mật khẩu?</h1>
      <p className="auth-card__sub">
        Nhập email hoặc tên đăng nhập. Chúng mình sẽ gửi cho bạn một đường dẫn để đặt lại
        mật khẩu.
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
            Email hoặc tên đăng nhập
          </label>
          <div className="field">
            <IconUser className="field__icon" />
            <input
              id={idOTim}
              className="field__input"
              value={identifier}
              placeholder="Email hoặc tên đăng nhập của bạn"
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
            {loading ? 'Đang gửi…' : 'Gửi hướng dẫn đặt lại'}
          </button>
        </>
      )}

      {footer && (
        <>
          <div className="auth-card__or">
            <span>hoặc</span>
          </div>
          <p className="auth-card__footer">{footer}</p>
        </>
      )}
    </form>
  );
}
