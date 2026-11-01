/**
 * Đua request (audit 2026-10-06): mở quán A rồi mở ngay quán B → phản hồi CŨ của A về
 * sau không được đè chi tiết của B, và `finally` của A không được tắt `loading` của B.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook } from '@testing-library/react';

type Hua = { resolve: (v: unknown) => void; reject: (e: unknown) => void; signal?: AbortSignal };
const dangCho = new Map<string, Hua>();
const restaurantDetail = vi.fn();

vi.mock('@/shared/api', async () => {
  const that = await vi.importActual<typeof import('@/shared/api')>('@/shared/api');
  return {
    ...that,
    api: { restaurantDetail: (...a: unknown[]) => restaurantDetail(...a) },
  };
});

import { ApiError } from '@/shared/api';
import { useRestaurantDetail } from './useRestaurantDetail';

function giaLapCham() {
  restaurantDetail.mockImplementation(
    (id: string, opts?: { signal?: AbortSignal }) =>
      new Promise((resolve, reject) => {
        dangCho.set(id, { resolve, reject, signal: opts?.signal });
        opts?.signal?.addEventListener('abort', () =>
          reject(Object.assign(new Error('aborted'), { name: 'AbortError' })),
        );
      }),
  );
}

afterEach(() => {
  dangCho.clear();
  restaurantDetail.mockReset();
});

describe('useRestaurantDetail', () => {
  it('phan hoi cu ve SAU khong de chi tiet moi, va khong tat loading cua request moi', async () => {
    giaLapCham();
    const { result } = renderHook(() => useRestaurantDetail());

    act(() => void result.current.load('A'));
    act(() => void result.current.load('B'));
    expect(result.current.loading).toBe(true);

    // A về muộn (giả sử server không tôn trọng abort và vẫn trả về).
    await act(async () => {
      dangCho.get('A')!.resolve({ restaurant_id: 'A', has_details: false });
      await Promise.resolve();
    });
    expect(result.current.detail).toBeNull();
    expect(result.current.loading).toBe(true);

    await act(async () => {
      dangCho.get('B')!.resolve({ restaurant_id: 'B', has_details: false });
      await Promise.resolve();
    });
    expect(result.current.detail).toMatchObject({ restaurant_id: 'B' });
    expect(result.current.loading).toBe(false);
  });

  it('request cu bi huy qua AbortSignal', () => {
    giaLapCham();
    const { result } = renderHook(() => useRestaurantDetail());
    act(() => void result.current.load('A'));
    act(() => void result.current.load('B'));
    expect(dangCho.get('A')!.signal?.aborted).toBe(true);
    expect(dangCho.get('B')!.signal?.aborted).toBe(false);
  });

  it('clear() huy request dang bay va tat loading', async () => {
    giaLapCham();
    const { result } = renderHook(() => useRestaurantDetail());
    act(() => void result.current.load('A'));
    act(() => result.current.clear());
    expect(result.current.loading).toBe(false);
    await act(async () => {
      dangCho.get('A')!.resolve({ restaurant_id: 'A', has_details: false });
      await Promise.resolve();
    });
    expect(result.current.detail).toBeNull();
  });

  it('404 bat co notFound chu khong hien loi "thu lai"', async () => {
    restaurantDetail.mockRejectedValue(
      new ApiError('RESTAURANT_NOT_FOUND', 'khong co', {}, 404),
    );
    const { result } = renderHook(() => useRestaurantDetail());
    await act(async () => {
      await result.current.load('X');
    });
    expect(result.current.notFound).toBe(true);
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });
});
