/**
 * Ràng buộc: ĐĂNG XUẤT từ thanh trên phải đưa người dùng về TRANG CHỦ.
 * Lỗi thật đã có: `onConfirm={session.logout}` chỉ xoá phiên, người dùng đứng lại ở
 * trang tài khoản (hồ sơ, yêu thích) đã không còn nội dung hợp lệ.
 */
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';
import { UserSessionProvider } from '@/entities/user';
import { LanguageProvider } from '@/shared/i18n';
import { SiteHeader } from './SiteHeader';

function gia_lap_fetch() {
  return vi.fn().mockImplementation((url: string) => {
    const tra = (data: unknown) =>
      Promise.resolve({ ok: true, status: 200, json: async () => ({ data }) });
    if (String(url).includes('/auth/me'))
      return tra({ user_id: 'u1', username: 'mung', role: 'user', display_name: 'Mùng' });
    return tra({});
  });
}

/** Hiện đường dẫn hiện tại để test đọc được việc điều hướng. */
function DoDuongDan() {
  const vi_tri = useLocation();
  return <div data-testid="duong-dan">{vi_tri.pathname}</div>;
}

function Khung({ children }: { children: ReactNode }) {
  return (
    <LanguageProvider>
      <UserSessionProvider>{children}</UserSessionProvider>
    </LanguageProvider>
  );
}

describe('SiteHeader — đăng xuất', () => {
  it('đăng xuất xong thì về trang chủ, không đứng lại ở trang tài khoản', async () => {
    sessionStorage.setItem('moodbite.user.token', 'token-gia-lap');
    vi.stubGlobal('fetch', gia_lap_fetch());

    render(
      <Khung>
        <MemoryRouter initialEntries={['/account']}>
          <SiteHeader />
          <Routes>
            <Route path="/account" element={<DoDuongDan />} />
            <Route path="/" element={<DoDuongDan />} />
          </Routes>
        </MemoryRouter>
      </Khung>,
    );

    // Chờ phiên tải xong để nút đăng xuất hiện (nút chỉ có khi đã đăng nhập).
    const nutDangXuat = await screen.findByRole('button', { name: 'Đăng xuất' });
    fireEvent.click(nutDangXuat);
    // Bấm đăng xuất mới chỉ MỞ hộp hỏi; phải xác nhận trong hộp thì mới đăng xuất thật.
    fireEvent.click(hopXacNhan());

    await waitFor(() => expect(screen.getByTestId('duong-dan')).toHaveTextContent(/^\/$/));
    expect(sessionStorage.getItem('moodbite.user.token')).toBeNull();
  });
});

/** Nút "Đăng xuất" trong hộp xác nhận (cùng nhãn với nút mở hộp, nên lấy theo lớp CSS). */
function hopXacNhan(): HTMLElement {
  const hop = screen.getByRole('alertdialog');
  return hop.querySelector('.xac-nhan__dong-y') as HTMLElement;
}
