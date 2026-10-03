/**
 * Form đăng nhập theo NGÔN NGỮ (thêm 2026-10-02): một lượt rà trình duyệt thật ở chế độ EN
 * thấy cả form vẫn tiếng Việt. Khoá lại: chọn 'en' thì nhãn/nút/placeholder là tiếng Anh,
 * còn mặc định vẫn đúng câu tiếng Việt cũ.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { LanguageProvider } from '@/shared/i18n';
import { LoginForm } from './LoginForm';

function renderForm() {
  return render(
    <MemoryRouter>
      <LanguageProvider>
        <LoginForm loading={false} error={null} onSubmit={vi.fn()} footer="x" />
      </LanguageProvider>
    </MemoryRouter>,
  );
}

afterEach(() => localStorage.clear());

describe('LoginForm - song ngu', () => {
  it('mac dinh van la tieng Viet', () => {
    renderForm();
    expect(screen.getByRole('heading', { name: /Chào mừng trở lại!/ })).toBeInTheDocument();
    expect(screen.getByLabelText('Tên đăng nhập')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Đăng nhập' })).toBeInTheDocument();
  });

  it('chon en thi nhan, placeholder va nut deu la tieng Anh', () => {
    localStorage.setItem('moodbite.lang', 'en');
    renderForm();
    expect(screen.getByRole('heading', { name: /Welcome back!/ })).toBeInTheDocument();
    expect(screen.getByLabelText('Username')).toHaveAttribute('placeholder', 'Enter your username');
    expect(screen.getByLabelText('Password')).toHaveAttribute('placeholder', 'Enter your password');
    expect(screen.getByText('Remember me')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Forgot password?' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Show password' })).toBeInTheDocument();
    expect(screen.getByText('or')).toBeInTheDocument();
    // Không còn sót chữ có dấu nào trong form.
    expect(document.body.textContent).not.toMatch(/[ăâđêôơưàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ]/i);
  });
});
