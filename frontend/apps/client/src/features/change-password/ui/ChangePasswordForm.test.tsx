/**
 * Test form ĐỔI MẬT KHẨU khi đang đăng nhập.
 *
 * Từ 2026-09-29 đổi mật khẩu THU HỒI mọi token, kể cả token của máy đang gọi, và server
 * trả token MỚI cho máy này. Điều dễ làm sai nhất: quên lưu token mới -> người dùng vừa
 * đổi mật khẩu thành công đã bị đá ra ở lần gọi kế tiếp.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

const changePassword = vi.fn();

vi.mock('@/shared/api', () => ({
  authApi: { changePassword: (...args: unknown[]) => changePassword(...args) },
}));

import { ChangePasswordForm } from './ChangePasswordForm';

const KEY = 'moodbite.user.token';

function guiForm(container: HTMLElement) {
  const [cu, moi] = Array.from(
    container.querySelectorAll<HTMLInputElement>('input[type="password"]'),
  );
  fireEvent.change(cu, { target: { value: 'mat-khau-cu-dai' } });
  fireEvent.change(moi, { target: { value: 'mat-khau-moi-dai' } });
  fireEvent.submit(container.querySelector('form')!);
}

beforeEach(() => {
  changePassword.mockReset();
  localStorage.clear();
  sessionStorage.clear();
});

afterEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});

describe('ChangePasswordForm', () => {
  it('lưu TOKEN MỚI server trả về, giữ nguyên lựa chọn "ghi nhớ" (localStorage)', async () => {
    localStorage.setItem(KEY, 'token-cu');
    changePassword.mockResolvedValue({
      message: 'Đã đổi mật khẩu. Các thiết bị khác đã bị đăng xuất.',
      token: 'token-moi',
      token_type: 'bearer',
      expires_in: 86400,
    });

    const { container } = render(<ChangePasswordForm />);
    guiForm(container);

    expect(await screen.findByText(/Các thiết bị khác đã bị đăng xuất/)).toBeInTheDocument();
    expect(localStorage.getItem(KEY)).toBe('token-moi');
    expect(sessionStorage.getItem(KEY)).toBeNull();
  });

  it('phiên tạm (sessionStorage) thì token mới cũng ở phiên tạm', async () => {
    sessionStorage.setItem(KEY, 'token-cu');
    changePassword.mockResolvedValue({
      message: 'ok', token: 'token-moi', token_type: 'bearer', expires_in: 86400,
    });

    const { container } = render(<ChangePasswordForm />);
    guiForm(container);

    await screen.findByText('ok');
    expect(sessionStorage.getItem(KEY)).toBe('token-moi');
    expect(localStorage.getItem(KEY)).toBeNull();
  });

  it('đổi hỏng thì KHÔNG đụng vào token đang có', async () => {
    localStorage.setItem(KEY, 'token-cu');
    changePassword.mockRejectedValue(new Error('Mật khẩu hiện tại không đúng.'));

    const { container } = render(<ChangePasswordForm />);
    guiForm(container);

    expect(await screen.findByText('Mật khẩu hiện tại không đúng.')).toBeInTheDocument();
    expect(localStorage.getItem(KEY)).toBe('token-cu');
  });
});
