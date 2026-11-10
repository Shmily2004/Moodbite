/**
 * Hoàn tác lạc quan (audit 2026-10-06): lưu A rồi lưu B thật nhanh, A lỗi → chỉ A bị gỡ,
 * B KHÔNG được biến mất (bản cũ `setItems(truoc)` trả về ảnh chụp lúc lưu A).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';

const saveFavorite = vi.fn();
const removeFavorite = vi.fn();
const favorites = vi.fn();
const me = vi.fn();

vi.mock('@/shared/api', async () => {
  const that = await vi.importActual<typeof import('@/shared/api')>('@/shared/api');
  return {
    ...that,
    authApi: {
      me: (...a: unknown[]) => me(...a),
      favorites: (...a: unknown[]) => favorites(...a),
      saveFavorite: (...a: unknown[]) => saveFavorite(...a),
      removeFavorite: (...a: unknown[]) => removeFavorite(...a),
      logout: () => Promise.resolve({}),
    },
  };
});

import { UserSessionProvider } from '@/entities/user';
import { useFavorites } from './useFavorites';

const wrapper = ({ children }: { children: ReactNode }) => (
  <MemoryRouter initialEntries={['/recommend?mood=relaxed']}>
    <UserSessionProvider>{children}</UserSessionProvider>
  </MemoryRouter>
);

/** Hiện đường dẫn + state hiện tại để test đọc được việc điều hướng. */
function DoDuongDan() {
  const vi_tri = useLocation();
  return (
    <div data-testid="duong-dan" data-from={(vi_tri.state as { from?: string } | null)?.from ?? ''}>
      {vi_tri.pathname}
    </div>
  );
}

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  sessionStorage.setItem('moodbite.user.token', 'tok');
  me.mockReturnValue(new Promise(() => undefined));
  favorites.mockResolvedValue({ items: [], total: 0 });
});

afterEach(() => {
  vi.clearAllMocks();
  sessionStorage.clear();
});

describe('useFavorites.toggle - hoan tac dung muc', () => {
  it('luu A roi B, A loi -> chi A bi go, B van con', async () => {
    let tuChoiA: (e: unknown) => void = () => undefined;
    saveFavorite.mockImplementation((body: { item_id: string }) =>
      body.item_id === 'A'
        ? new Promise((_, reject) => {
            tuChoiA = reject;
          })
        : Promise.resolve({}),
    );

    const { result } = renderHook(() => useFavorites(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => result.current.toggle({ itemType: 'dish', itemId: 'A', name: 'Món A' }));
    act(() => result.current.toggle({ itemType: 'dish', itemId: 'B', name: 'Món B' }));
    expect(result.current.items.map((x) => x.itemId).sort()).toEqual(['A', 'B']);

    await act(async () => {
      tuChoiA(new Error('mất mạng'));
      await Promise.resolve();
    });

    expect(result.current.items.map((x) => x.itemId)).toEqual(['B']);
    expect(result.current.error).not.toBeNull();
  });

  it('bo luu loi -> muc quay lai, muc khac khong bi anh huong', async () => {
    favorites.mockResolvedValue({
      items: [
        { item_type: 'dish', item_id: 'A', name: 'Món A', list_type: 'favorite' },
      ],
      total: 1,
    });
    let tuChoi: (e: unknown) => void = () => undefined;
    removeFavorite.mockImplementation(
      () =>
        new Promise((_, reject) => {
          tuChoi = reject;
        }),
    );
    saveFavorite.mockResolvedValue({});

    const { result } = renderHook(() => useFavorites(), { wrapper });
    await waitFor(() => expect(result.current.items).toHaveLength(1));

    act(() => result.current.toggle({ itemType: 'dish', itemId: 'A', name: 'Món A' }));
    act(() => result.current.toggle({ itemType: 'dish', itemId: 'C', name: 'Món C' }));
    expect(result.current.items.map((x) => x.itemId)).toEqual(['C']);

    await act(async () => {
      tuChoi(new Error('lỗi'));
      await Promise.resolve();
    });
    expect(result.current.items.map((x) => x.itemId).sort()).toEqual(['A', 'C']);
  });
});

describe('useFavorites.toggle - khách (chưa đăng nhập)', () => {
  it('bấm lưu khi chưa đăng nhập: chuyển sang đăng nhập, KHÔNG ghi gì lên máy', async () => {
    sessionStorage.clear(); // không có token = khách
    const khachWrapper = ({ children }: { children: ReactNode }) => (
      <MemoryRouter initialEntries={['/recommend?mood=relaxed']}>
        <UserSessionProvider>
          <Routes>
            <Route path="/login" element={<DoDuongDan />} />
            <Route path="*" element={children} />
          </Routes>
        </UserSessionProvider>
      </MemoryRouter>
    );
    const { result } = renderHook(() => useFavorites(), { wrapper: khachWrapper });

    act(() => result.current.toggle({ itemType: 'dish', itemId: 'A', name: 'Món A' }));

    expect(saveFavorite).not.toHaveBeenCalled();
    expect(result.current.items).toEqual([]);
    expect(localStorage.length).toBe(0);
  });

  it('bấm lưu khi chưa đăng nhập: đường dẫn đăng nhập mang theo trang đang xem', async () => {
    sessionStorage.clear();
    const ghi: { pathname: string; from: string } = { pathname: '', from: '' };
    function Ghi() {
      const vi_tri = useLocation();
      ghi.pathname = vi_tri.pathname;
      ghi.from = (vi_tri.state as { from?: string } | null)?.from ?? '';
      return null;
    }
    const khachWrapper = ({ children }: { children: ReactNode }) => (
      <MemoryRouter initialEntries={['/recommend?mood=relaxed']}>
        <UserSessionProvider>
          <Ghi />
          <Routes>
            <Route path="/login" element={<DoDuongDan />} />
            <Route path="*" element={children} />
          </Routes>
        </UserSessionProvider>
      </MemoryRouter>
    );
    const { result } = renderHook(() => useFavorites(), { wrapper: khachWrapper });

    act(() => result.current.toggle({ itemType: 'dish', itemId: 'A', name: 'Món A' }));

    await waitFor(() => expect(ghi.pathname).toBe('/login'));
    expect(ghi.from).toBe('/recommend?mood=relaxed');
  });
});

