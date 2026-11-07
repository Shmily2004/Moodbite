/**
 * Đăng nhập CHUNG (2026-11-01): tài khoản admin đăng nhập ở `/login` phải có thêm phiên
 * quản trị; nếu bước đó lỗi thì phiên khách KHÔNG được lưu.
 *
 * Giả `fetch` theo đường dẫn để đi qua đúng lớp HttpClient thật (envelope `{data}`/`{error}`).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import { useUserSession } from '@/entities/user';
import { quanTriSauDangNhap } from './quanTriSauDangNhap';

const KHACH = 'moodbite.user.token';
const QUAN_TRI = 'moodbite.admin.token';

function nguoi(role: string) {
  return {
    user_id: 'u1',
    username: 'quantri',
    role,
    display_name: 'Quản trị viên',
    email: null,
    email_verified: false,
    created_at: '2026-11-01T00:00:00+00:00',
  };
}

function gia_lap(role: string, quanTri: { status: number; body: unknown }) {
  return vi.fn().mockImplementation((url: string) => {
    const duong = String(url);
    if (duong.includes('/auth/login')) {
      return Promise.resolve(
        new Response(JSON.stringify({ data: { token: 'token-khach', user: nguoi(role) } }), {
          status: 200,
        }),
      );
    }
    if (duong.includes('/admin/login')) {
      return Promise.resolve(new Response(JSON.stringify(quanTri.body), { status: quanTri.status }));
    }
    return Promise.reject(new Error('không có trong test: ' + duong));
  });
}

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
  sessionStorage.clear();
});

describe('quanTriSauDangNhap', () => {
  it('tài khoản admin: đăng nhập xong có thêm phiên quản trị, và phiên khách được lưu', async () => {
    const fetchMock = gia_lap('admin', {
      status: 200,
      body: { data: { token: 'token-quan-tri', token_type: 'bearer', expires_in: 3600 } },
    });
    vi.stubGlobal('fetch', fetchMock);
    const { result } = renderHook(() => useUserSession());

    await act(() =>
      result.current.login('quantri', 'mat-khau-du-dai', true, quanTriSauDangNhap('quantri', 'mat-khau-du-dai')),
    );

    expect(fetchMock.mock.calls.some(([u]) => String(u).includes('/admin/login'))).toBe(true);
    expect(sessionStorage.getItem(QUAN_TRI)).toBe('token-quan-tri');
    expect(localStorage.getItem(KHACH)).toBe('token-khach');
    expect(result.current.isLoggedIn).toBe(true);
  });

  it('tài khoản thường: KHÔNG gọi /admin/login và không có phiên quản trị', async () => {
    const fetchMock = gia_lap('user', { status: 200, body: {} });
    vi.stubGlobal('fetch', fetchMock);
    const { result } = renderHook(() => useUserSession());

    await act(() =>
      result.current.login('nguoidung', 'mat-khau-du-dai', true, quanTriSauDangNhap('nguoidung', 'mat-khau-du-dai')),
    );

    expect(fetchMock.mock.calls.some(([u]) => String(u).includes('/admin/login'))).toBe(false);
    expect(sessionStorage.getItem(QUAN_TRI)).toBeNull();
    expect(result.current.isLoggedIn).toBe(true);
  });

  it('admin mà máy chủ không lấy được phiên quản trị: KHÔNG lưu phiên khách, báo đúng câu lỗi', async () => {
    // Quyết định đã chốt: không cho admin vào app khách một nửa.
    vi.stubGlobal(
      'fetch',
      gia_lap('admin', {
        status: 503,
        body: { error: { code: 'DATA_NOT_READY', message: 'Chưa đặt MOODBITE_ADMIN_SECRET.' } },
      }),
    );
    const { result } = renderHook(() => useUserSession());

    await act(() =>
      result.current.login('quantri', 'mat-khau-du-dai', true, quanTriSauDangNhap('quantri', 'mat-khau-du-dai')),
    );

    expect(localStorage.getItem(KHACH)).toBeNull();
    expect(sessionStorage.getItem(KHACH)).toBeNull();
    expect(result.current.isLoggedIn).toBe(false);
    expect(result.current.error).toContain('MOODBITE_ADMIN_SECRET');
  });
});
