/**
 * ViewModel "Bộ sưu tập": gọi đúng endpoint, cập nhật danh sách theo bản SERVER trả về,
 * và hiện NGUYÊN VĂN câu lỗi của server (luật tên/giới hạn chỉ nằm ở backend).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { UserSessionProvider } from '@/entities/user';
import { useCollections } from './useCollections';

const BO = {
  collection_id: 'c1',
  name: 'Hẹn hò',
  created_at: '2026-09-29T00:00:00+00:00',
  item_count: 0,
  items: [],
};

type Goi = { url: string; method: string; body: unknown };

function gia_lap_fetch(ds: unknown[], goi: Goi[]) {
  return vi.fn().mockImplementation((url: string, init?: RequestInit) => {
    const method = init?.method ?? 'GET';
    const body = init?.body ? JSON.parse(String(init.body)) : null;
    goi.push({ url: String(url), method, body });
    const tra = (data: unknown, status = 200) =>
      Promise.resolve({ ok: status < 400, status, json: async () => ({ data }) });
    const u = String(url);
    if (u.includes('/auth/me')) return tra({ user_id: 'u1', username: 'mung', role: 'user' });
    if (u.endsWith('/me/collections') && method === 'GET')
      return tra({ collections: ds, total: ds.length });
    if (u.endsWith('/me/collections') && method === 'POST') {
      if ((body as { name: string }).name.length > 60)
        return Promise.resolve({
          ok: false,
          status: 400,
          json: async () => ({
            error: { code: 'INVALID_REQUEST', message: 'Tên bộ sưu tập tối đa 60 ký tự (đang có 61).', details: {} },
          }),
        });
      return tra({ ...BO, collection_id: 'moi', name: (body as { name: string }).name }, 201);
    }
    if (u.includes('/items') && method === 'POST')
      return tra({ ...BO, item_count: 1, items: [{ ...(body as object), added_at: null }] });
    if (method === 'DELETE') return tra({ message: 'ok' });
    return tra({});
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

describe('useCollections', () => {
  it('tai danh sach va doi sang camelCase', async () => {
    vi.stubGlobal('fetch', gia_lap_fetch([BO], []));
    const { result } = renderHook(() => useCollections(), { wrapper });
    await waitFor(() => expect(result.current.collections).toHaveLength(1));
    expect(result.current.collections[0]).toEqual({
      id: 'c1',
      name: 'Hẹn hò',
      itemCount: 0,
      items: [],
    });
  });

  it('tao moi dua bo len DAU danh sach', async () => {
    vi.stubGlobal('fetch', gia_lap_fetch([BO], []));
    const { result } = renderHook(() => useCollections(), { wrapper });
    await waitFor(() => expect(result.current.collections).toHaveLength(1));
    await act(async () => {
      await result.current.create('Quán gần công ty');
    });
    expect(result.current.collections.map((b) => b.name)).toEqual([
      'Quán gần công ty',
      'Hẹn hò',
    ]);
  });

  it('server tu choi ten -> hien NGUYEN VAN cau loi, danh sach khong doi', async () => {
    vi.stubGlobal('fetch', gia_lap_fetch([BO], []));
    const { result } = renderHook(() => useCollections(), { wrapper });
    await waitFor(() => expect(result.current.collections).toHaveLength(1));
    let kq: unknown = 'chua';
    await act(async () => {
      kq = await result.current.create('x'.repeat(61));
    });
    expect(kq).toBeNull();
    expect(result.current.error).toBe('Tên bộ sưu tập tối đa 60 ký tự (đang có 61).');
    expect(result.current.collections).toHaveLength(1);
  });

  it('them muc gui dung snake_case va thay bo bang ban server tra ve', async () => {
    const goi: Goi[] = [];
    vi.stubGlobal('fetch', gia_lap_fetch([BO], goi));
    const { result } = renderHook(() => useCollections(), { wrapper });
    await waitFor(() => expect(result.current.collections).toHaveLength(1));
    await act(async () => {
      await result.current.addItem('c1', { itemType: 'dish', itemId: 'pho-bo', name: 'Phở bò' });
    });
    const post = goi.find((g) => g.method === 'POST' && g.url.includes('/me/collections/c1/items'));
    expect(post?.body).toEqual({ item_type: 'dish', item_id: 'pho-bo', name: 'Phở bò' });
    expect(result.current.collections[0].itemCount).toBe(1);
  });

  it('xoa bo goi DELETE dung ma va bo khoi danh sach', async () => {
    const goi: Goi[] = [];
    vi.stubGlobal('fetch', gia_lap_fetch([BO], goi));
    const { result } = renderHook(() => useCollections(), { wrapper });
    await waitFor(() => expect(result.current.collections).toHaveLength(1));
    await act(async () => {
      await result.current.remove('c1');
    });
    expect(goi.some((g) => g.method === 'DELETE' && g.url.endsWith('/me/collections/c1'))).toBe(true);
    expect(result.current.collections).toEqual([]);
  });
});
