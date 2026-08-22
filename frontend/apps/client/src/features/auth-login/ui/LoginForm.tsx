/**
 * VIEW: form đăng nhập. Chỉ JSX + state của riêng ô nhập, mọi thứ khác nhận qua props.
 *
 * Không gọi API ở đây (đúng luật FSD/MVVM của dự án: `ui/` là VIEW, `model/` là
 * VIEWMODEL). Nhờ vậy test dựng form với `onSubmit` giả là xong, không cần mạng.
 */
import { useId, useState } from 'react';
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { IconEye, IconEyeOff, IconLock, IconUser } from '@/shared/ui';
import { ROUTES } from '@/shared/config';

export interface LoginFormProps {
  loading: boolean;
  error: string | null;
  onSubmit: (username: string, password: string, remember: boolean) => void;
  /** Nội dung xếp dưới đường kẻ "hoặc" — thường là link sang trang đăng ký. */
  footer?: ReactNode;
}

export function LoginForm({ loading, error, onSubmit, footer }: LoginFormProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(false);
  const [hienMatKhau, setHienMatKhau] = useState(false);

  // `useId` thay vì id gõ tay: trang đăng ký sau này có thể đặt hai form trên cùng một
  // trang, id trùng thì click vào nhãn sẽ nhảy nhầm ô.
  const idTen = useId();
  const idMatKhau = useId();
  const idGhiNho = useId();
  const idLoi = useId();

  return (
    <form
      className="auth-card"
      noValidate
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(username, password, remember);
      }}
    >
      <h1 className="auth-card__title">
        Chào mừng trở lại! <span aria-hidden="true">👋</span>
      </h1>
      <p className="auth-card__sub">
        Đăng nhập để khám phá những món ngon phù hợp với bạn ở Hà Nội.
      </p>

      <label className="field__label" htmlFor={idTen}>
        Tên đăng nhập
      </label>
      <div className="field">
        <IconUser className="field__icon" />
        <input
          id={idTen}
          className="field__input"
          value={username}
          placeholder="Nhập tên đăng nhập"
          autoComplete="username"
          // `autoFocus` trên trang đăng nhập là một trong số RẤT ÍT chỗ dùng nó hợp lý:
          // cả trang chỉ có một việc để làm, người dùng gõ được ngay không phải với chuột.
          autoFocus
          required
          onChange={(event) => setUsername(event.target.value)}
        />
      </div>

      <label className="field__label" htmlFor={idMatKhau}>
        Mật khẩu
      </label>
      <div className="field">
        <IconLock className="field__icon" />
        <input
          id={idMatKhau}
          className="field__input"
          type={hienMatKhau ? 'text' : 'password'}
          value={password}
          placeholder="Nhập mật khẩu"
          autoComplete="current-password"
          required
          onChange={(event) => setPassword(event.target.value)}
        />
        <button
          type="button"
          className="field__eye"
          onClick={() => setHienMatKhau((cu) => !cu)}
          aria-label={hienMatKhau ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
          aria-pressed={hienMatKhau}
          // `tabIndex={-1}`: người dùng bàn phím gõ xong mật khẩu là muốn tới nút Đăng
          // nhập, không muốn dừng ở con mắt.
          tabIndex={-1}
        >
          {hienMatKhau ? <IconEyeOff /> : <IconEye />}
        </button>
      </div>

      <div className="auth-card__row">
        <label className="checkbox" htmlFor={idGhiNho}>
          <input
            id={idGhiNho}
            type="checkbox"
            checked={remember}
            onChange={(event) => setRemember(event.target.checked)}
          />
          <span>Ghi nhớ đăng nhập</span>
        </label>

        {/* Từ 2026-08-22 đây là LINK THẬT: tính năng gửi thư đặt lại mật khẩu đã làm
            xong (`/auth/forgot-password`). Trước đó nó chỉ mở ra một dòng giải thích. */}
        <Link className="linkish" to={ROUTES.forgotPassword}>
          Quên mật khẩu?
        </Link>
      </div>

      {error && (
        <p className="auth-card__error" id={idLoi} role="alert">
          {error}
        </p>
      )}

      <button type="submit" className="btn btn--primary" disabled={loading}>
        {loading ? 'Đang đăng nhập…' : 'Đăng nhập'}
      </button>

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
