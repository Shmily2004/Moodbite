/** VIEW: form đăng nhập. Chỉ JSX, nhận mọi thứ qua props. */
import { useState } from 'react';

export interface LoginFormProps {
  loading: boolean;
  error: string | null;
  onSubmit: (username: string, password: string) => void;
}

export function LoginForm({ loading, error, onSubmit }: LoginFormProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  return (
    <form
      className="card login"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(username, password);
      }}
    >
      <h1>MoodBite — Quản trị</h1>
      <p className="muted">Trang này chỉ dành cho người quản lý dữ liệu quán.</p>

      <label htmlFor="username">Tên đăng nhập</label>
      <input
        id="username"
        value={username}
        autoComplete="username"
        onChange={(event) => setUsername(event.target.value)}
        required
      />

      <label htmlFor="password">Mật khẩu</label>
      <input
        id="password"
        type="password"
        value={password}
        autoComplete="current-password"
        onChange={(event) => setPassword(event.target.value)}
        required
      />

      {error && <p className="error">{error}</p>}

      <button type="submit" disabled={loading}>
        {loading ? 'Đang đăng nhập…' : 'Đăng nhập'}
      </button>
    </form>
  );
}
