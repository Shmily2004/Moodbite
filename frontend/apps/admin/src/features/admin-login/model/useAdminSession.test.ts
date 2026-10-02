/**
 * Đăng xuất quản trị (2026-10-02): phải báo server thu hồi token KHI token còn trong kho,
 * và server lỗi thì VẪN đăng xuất khỏi máy này.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook } from '@testing-library/react';

const logout = vi.fn();

vi.mock('@/shared/api', async () => {
  const that = await vi.importActual<typeof import('@/shared/api')>('@/shared/api');
  return { ...that, adminApi: { logout: (...a: unknown[]) => logout(...a) } };
});

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
