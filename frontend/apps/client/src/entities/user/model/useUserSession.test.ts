/**
 * Test ĐĂNG XUẤT của phiên người dùng.
 *
 * Từ 2026-09-29 đăng xuất báo server THU HỒI token. Hai điều phải khoá:
 *   1. gọi `/auth/logout` KHI token còn trong kho (xoá trước thì server không biết thu
 *      hồi của ai)
 *   2. server lỗi/mất mạng thì VẪN đăng xuất khỏi máy này
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook } from '@testing-library/react';

const KEY = 'moodbite.user.token';
const logout = vi.fn();
const me = vi.fn();

vi.mock('@/shared/api', async () => {
  const that = await vi.importActual<typeof import('@/shared/api')>('@/shared/api');
  return {
    ...that,
    authApi: {
      me: (...a: unknown[]) => me(...a),
      logout: (...a: unknown[]) => logout(...a),
    },
  };
});

import { useUserSession } from './useUserSession';

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  logout.mockReset();
  me.mockReset();
  me.mockReturnValue(new Promise(() => undefined));
});

afterEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});

describe('useUserSession.logout', () => {
  it('gọi server thu hồi TRONG LÚC token còn trong kho, rồi mới xoá', () => {
    localStorage.setItem(KEY, 'token-dang-dung');
    let token_luc_goi: string | null = 'chua-goi';
    logout.mockImplementation(() => {
      token_luc_goi = localStorage.getItem(KEY);
      return Promise.resolve({ message: 'ok' });
    });

    const { result } = renderHook(() => useUserSession());
    act(() => result.current.logout());

    expect(logout).toHaveBeenCalledTimes(1);
    expect(token_luc_goi).toBe('token-dang-dung');
    expect(localStorage.getItem(KEY)).toBeNull();
    expect(result.current.isLoggedIn).toBe(false);
  });

  it('server lỗi thì VẪN đăng xuất khỏi máy này', async () => {
    localStorage.setItem(KEY, 'token-dang-dung');
    logout.mockRejectedValue(new Error('mất mạng'));

    const { result } = renderHook(() => useUserSession());
    await act(async () => {
      result.current.logout();
      await Promise.resolve();
    });

    expect(localStorage.getItem(KEY)).toBeNull();
    expect(result.current.isLoggedIn).toBe(false);
  });
});
