/**
 * Phiên QUẢN TRỊ (2026-11-01): không còn đăng nhập ở đây — đăng nhập ở trang chung. Test
 * này khoá ba việc còn lại: đăng xuất phải báo server thu hồi token KHI token còn trong kho,
 * server lỗi thì vẫn đăng xuất khỏi máy này, và đăng xuất quản trị phải đăng xuất cả khách.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook } from '@testing-library/react';

const logout = vi.fn();

vi.mock('@admin/shared/api', async () => {
  const that = await vi.importActual<typeof import('@admin/shared/api')>('@admin/shared/api');
  return {
    ...that,
    adminApi: {
      logout: (...a: unknown[]) => logout(...a),
    },
  };
});

import { readToken, writeToken } from '@admin/shared/lib';
import { useAdminSession } from './useAdminSession';
import { PHAT_DANG_XUAT_KHACH } from './phienQuanTri';

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

  it('đăng xuất quản trị phát sự kiện để app người dùng đăng xuất theo', () => {
    writeToken('token-quan-tri');
    logout.mockResolvedValue({ message: 'ok' });
    const nghe = vi.fn();
    window.addEventListener(PHAT_DANG_XUAT_KHACH, nghe);

    const { result } = renderHook(() => useAdminSession());
    act(() => result.current.logout());

    expect(nghe).toHaveBeenCalledTimes(1);
    window.removeEventListener(PHAT_DANG_XUAT_KHACH, nghe);
  });
});

describe('useAdminSession - 401 ở BẤT KỲ trang nào (audit 2026-10-06)', () => {
  it('handleUnauthorized với token hiện tại -> đăng xuất và báo hết hạn', async () => {
    const { handleUnauthorized } = await import('@admin/shared/lib');
    writeToken('tok-a');
    const { result } = renderHook(() => useAdminSession());
    expect(result.current.isLoggedIn).toBe(true);

    act(() => handleUnauthorized('tok-a'));

    expect(result.current.isLoggedIn).toBe(false);
    expect(readToken()).toBeNull();
  });

  it('401 của token cũ -> bỏ qua', async () => {
    const { handleUnauthorized } = await import('@admin/shared/lib');
    writeToken('tok-moi');
    const { result } = renderHook(() => useAdminSession());
    act(() => handleUnauthorized('tok-cu'));
    expect(result.current.isLoggedIn).toBe(true);
  });
});
