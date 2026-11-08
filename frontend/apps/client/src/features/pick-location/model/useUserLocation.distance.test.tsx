/**
 * Quy tắc KHOẢNG CÁCH (ràng buộc nghiệp vụ): khách chưa đăng nhập KHÔNG được thấy khoảng
 * cách từ quán tới vị trí của mình, dù đã bấm "Vị trí của tôi" và trình duyệt đã cấp quyền.
 * Đã đăng nhập và có vị trí thật thì mới hiện.
 *
 * Lỗi thật đã có: `hienKhoangCach={!isDefault}` cho khách hiện km sau khi định vị.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { UserSessionProvider } from '@/entities/user';
import { useUserLocation } from './useUserLocation';

const TOA_DO_DINH_VI = { latitude: 21.0368, longitude: 105.7826 };

function cap_quyen_dinh_vi() {
  Object.defineProperty(navigator, 'geolocation', {
    configurable: true,
    value: {
      getCurrentPosition: (ok: (p: { coords: typeof TOA_DO_DINH_VI }) => void) =>
        ok({ coords: TOA_DO_DINH_VI }),
    },
  });
}

function gia_lap_fetch() {
  return vi.fn().mockImplementation((url: string) => {
    const tra = (data: unknown) =>
      Promise.resolve({ ok: true, status: 200, json: async () => ({ data }) });
    if (String(url).includes('/auth/me'))
      return tra({ user_id: 'u1', username: 'mung', role: 'user' });
    if (String(url).includes('/me/addresses')) return tra({ addresses: [], total: 0 });
    return tra({});
  });
}

const wrapper = ({ children }: { children: ReactNode }) => (
  <UserSessionProvider>{children}</UserSessionProvider>
);

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  cap_quyen_dinh_vi();
});

describe('canShowDistance — quy tắc hiện khoảng cách', () => {
  it('khách chưa đăng nhập: đã định vị thật nhưng KHÔNG được hiện khoảng cách', async () => {
    vi.stubGlobal('fetch', gia_lap_fetch());
    const { result } = renderHook(() => useUserLocation(), { wrapper });

    act(() => result.current.request());

    await waitFor(() => expect(result.current.source).toBe('browser'));
    expect(result.current.isDefault).toBe(false);
    expect(result.current.canShowDistance).toBe(false);
  });

  it('khách chưa định vị: không hiện khoảng cách (đang ở trung tâm Hà Nội)', () => {
    vi.stubGlobal('fetch', gia_lap_fetch());
    const { result } = renderHook(() => useUserLocation(), { wrapper });
    expect(result.current.canShowDistance).toBe(false);
  });

  it('đã đăng nhập và đã định vị: được hiện khoảng cách', async () => {
    sessionStorage.setItem('moodbite.user.token', 'token-gia-lap');
    vi.stubGlobal('fetch', gia_lap_fetch());
    const { result } = renderHook(() => useUserLocation(), { wrapper });

    act(() => result.current.request());

    await waitFor(() => expect(result.current.canShowDistance).toBe(true));
    expect(result.current.source).toBe('browser');
  });
});
