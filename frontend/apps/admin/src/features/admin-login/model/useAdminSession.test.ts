/**
 * Đăng xuất quản trị (2026-10-02): phải báo server thu hồi token KHI token còn trong kho,
 * và server lỗi thì VẪN đăng xuất khỏi máy này.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook } from '@testing-library/react';

const logout = vi.fn();
const login = vi.fn();

vi.mock('@/shared/api', async () => {
  const that = await vi.importActual<typeof import('@/shared/api')>('@/shared/api');
  return {
    ...that,
    adminApi: {
      logout: (...a: unknown[]) => logout(...a),
      login: (...a: unknown[]) => login(...a),
    },
  };
});

import { ApiError } from '@/shared/api';
import { readToken, writeToken } from '@/shared/lib';
import { useAdminSession } from './useAdminSession';

beforeEach(() => {
  sessionStorage.clear();
  logout.mockReset();
});

afterEach(() => sessionStorage.clear());

describe('useAdminSession.logout', () => {
  it('gọi server thu hồi trong lúc token còn trong kho, rồi mới xoá', () => {
    writeToken('token-quan-tri');
    let token_luc_goi: string | null = 'chua-goi';
    logout.mockImplementation(() => {
      token_luc_goi = readToken();
      return Promise.resolve({ message: 'ok' });
    });

    const { result } = renderHook(() => useAdminSession());
    act(() => result.current.logout());

    expect(logout).toHaveBeenCalledTimes(1);
    expect(token_luc_goi).toBe('token-quan-tri');
    expect(readToken()).toBeNull();
    expect(result.current.isLoggedIn).toBe(false);
  });

  it('server lỗi thì vẫn đăng xuất khỏi máy này', async () => {
    writeToken('token-quan-tri');
    logout.mockRejectedValue(new Error('mất mạng'));

    const { result } = renderHook(() => useAdminSession());
    await act(async () => {
      result.current.logout();
      await Promise.resolve();
    });

    expect(readToken()).toBeNull();
    expect(result.current.isLoggedIn).toBe(false);
  });
});

describe('useAdminSession.login - cau bao loi', () => {
  it('sai mat khau (401) hien DUNG cau backend, khong phai "phien het han"', async () => {
    login.mockRejectedValue(
      new ApiError('UNAUTHORIZED', 'Sai tên đăng nhập hoặc mật khẩu.', {}, 401),
    );
    const { result } = renderHook(() => useAdminSession());
    await act(() => result.current.login('admin', 'sai'));

    expect(result.current.error).toBe('Sai tên đăng nhập hoặc mật khẩu.');
    expect(result.current.isLoggedIn).toBe(false);
  });

  it('503 giu nguyen huong dan khac phuc cua backend', async () => {
    login.mockRejectedValue(
      new ApiError('DATA_NOT_READY', 'Chưa đặt MOODBITE_ADMIN_PASSWORD. Đặt biến rồi khởi động lại.', {}, 503),
    );
    const { result } = renderHook(() => useAdminSession());
    await act(() => result.current.login('admin', 'x'));

    expect(result.current.error).toContain('MOODBITE_ADMIN_PASSWORD');
  });

  it('mat mang thi dung cau de hieu thay vi "Failed to fetch"', async () => {
    login.mockRejectedValue(new ApiError('NETWORK', 'Failed to fetch'));
    const { result } = renderHook(() => useAdminSession());
    await act(() => result.current.login('admin', 'x'));

    expect(result.current.error).not.toContain('Failed to fetch');
    expect(result.current.error).toContain('Không kết nối được');
  });
});

describe('useAdminSession - 401 o BAT KY trang nao (audit 2026-10-06)', () => {
  it('handleUnauthorized voi token hien tai -> dang xuat + bao het han', async () => {
    const { handleUnauthorized } = await import('@/shared/lib');
    writeToken('tok-a');
    const { result } = renderHook(() => useAdminSession());
    expect(result.current.isLoggedIn).toBe(true);

    act(() => handleUnauthorized('tok-a'));

    expect(result.current.isLoggedIn).toBe(false);
    expect(result.current.error).toContain('hết hạn');
    expect(readToken()).toBeNull();
  });

  it('401 cua token cu -> bo qua', async () => {
    const { handleUnauthorized } = await import('@/shared/lib');
    writeToken('tok-moi');
    const { result } = renderHook(() => useAdminSession());
    act(() => handleUnauthorized('tok-cu'));
    expect(result.current.isLoggedIn).toBe(true);
  });
});
