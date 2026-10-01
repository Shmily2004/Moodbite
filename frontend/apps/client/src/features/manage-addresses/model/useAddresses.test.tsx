/**
 * ViewModel "Địa chỉ của tôi".
 *
 * Khoá hai điều: (1) mô tả bỏ trống gửi `null` chứ không gửi chuỗi rỗng — "không có dữ
 * liệu" khác "dữ liệu rỗng" (CLAUDE.md mục 4.1); (2) đặt mặc định xong thì TẢI LẠI từ
 * server chứ không tự đoán cờ của các địa chỉ khác — luật đó chỉ nằm ở backend.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { UserSessionProvider } from '@/entities/user';
import { useAddresses } from './useAddresses';

type Goi = { url: string; method: string; body: unknown };

const NHA = {
  address_id: 'a1', label: 'Nhà', address_text: null, lat: 21.03, lng: 105.85,
  is_default: true, created_at: null,
};
const CONG_TY = { ...NHA, address_id: 'a2', label: 'Công ty', is_default: false };

function gia_lap_fetch(goi: Goi[], lanTai: unknown[][]) {
  let lan = 0;
  return vi.fn().mockImplementation((url: string, init?: RequestInit) => {
    const method = init?.method ?? 'GET';
    goi.push({ url: String(url), method, body: init?.body ? JSON.parse(String(init.body)) : null });
    const tra = (data: unknown, status = 200) =>
      Promise.resolve({ ok: true, status, json: async () => ({ data }) });
    const u = String(url);
    if (u.includes('/auth/me')) return tra({ user_id: 'u1', username: 'mung', role: 'user' });
    if (u.endsWith('/me/addresses') && method === 'GET') {
      const ds = lanTai[Math.min(lan, lanTai.length - 1)];
      lan += 1;
      return tra({ addresses: ds, total: ds.length });
    }
    return tra({ ...NHA }, method === 'POST' ? 201 : 200);
  });
}

const wrapper = ({ children }: { children: ReactNode }) => (
  <UserSessionProvider>{children}</UserSessionProvider>
);

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  sessionStorage.setItem('moodbite.user.token', 'token-gia-lap');
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('useAddresses', () => {
  it('them dia chi: mo ta rong gui null, roi tai lai', async () => {
    const goi: Goi[] = [];
    vi.stubGlobal('fetch', gia_lap_fetch(goi, [[], [NHA]]));
    const { result } = renderHook(() => useAddresses(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.add({ label: 'Nhà', addressText: '   ', lat: 21.03, lng: 105.85 });
    });
    const post = goi.find((g) => g.method === 'POST');
    expect(post?.body).toEqual({ label: 'Nhà', lat: 21.03, lng: 105.85, address_text: null });
    await waitFor(() => expect(result.current.addresses).toHaveLength(1));
  });

  it('dat mac dinh: PATCH is_default roi lay co tu SERVER', async () => {
    const goi: Goi[] = [];
    vi.stubGlobal(
      'fetch',
      gia_lap_fetch(goi, [
        [NHA, CONG_TY],
        [{ ...CONG_TY, is_default: true }, { ...NHA, is_default: false }],
      ]),
    );
    const { result } = renderHook(() => useAddresses(), { wrapper });
    await waitFor(() => expect(result.current.addresses).toHaveLength(2));

    await act(async () => {
      await result.current.setDefault('a2', true);
    });
    const patch = goi.find((g) => g.method === 'PATCH');
    expect(patch?.url).toMatch(/\/me\/addresses\/a2$/);
    expect(patch?.body).toEqual({ is_default: true });
    await waitFor(() =>
      expect(result.current.addresses.filter((a) => a.is_default).map((a) => a.label)).toEqual([
        'Công ty',
      ]),
    );
  });
});
