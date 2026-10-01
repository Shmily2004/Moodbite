/**
 * Điểm dự phòng vị trí (2026-09-29): trình duyệt -> địa chỉ MẶC ĐỊNH đã lưu -> Hồ Gươm.
 *
 * Hai điều phải khoá:
 *   1. thứ tự ưu tiên đúng, và `label` NÓI RÕ điểm nào đang dùng (không đổi ngầm);
 *   2. trình duyệt từ chối thì câu lỗi nói đang dùng ĐỊA CHỈ ĐÃ LƯU chứ không phải
 *      "trung tâm Hà Nội" như trước — nói sai điểm là người dùng tưởng app định vị hỏng.
 *
 * Giả lập `fetch` (không mock `@/shared/api`) để đi qua đúng HttpClient thật.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { UserSessionProvider } from '@/entities/user';
import { HANOI_CENTER } from '@/shared/config';
import { chonViTri, useUserLocation } from './useUserLocation';

const NHA = { lat: 21.0368, lng: 105.7826, label: 'Nhà' };

function gia_lap_fetch(diaChi: unknown[]) {
  return vi.fn().mockImplementation((url: string) => {
    const tra = (data: unknown) =>
      Promise.resolve({ ok: true, status: 200, json: async () => ({ data }) });
    if (String(url).includes('/auth/me'))
      return tra({ user_id: 'u1', username: 'mung', role: 'user' });
    if (String(url).includes('/me/addresses'))
      return tra({ addresses: diaChi, total: diaChi.length });
    return tra({});
  });
}

const wrapper = ({ children }: { children: ReactNode }) => (
  <UserSessionProvider>{children}</UserSessionProvider>
);

function tu_choi_dinh_vi() {
  Object.defineProperty(navigator, 'geolocation', {
    configurable: true,
    value: {
      getCurrentPosition: (_ok: unknown, loi: (e: { code: number }) => void) => loi({ code: 1 }),
    },
  });
}

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('chonViTri', () => {
  it('uu tien vi tri trinh duyet', () => {
    const kq = chonViTri({ lat: 21.01, lng: 105.8 }, NHA);
    expect(kq.source).toBe('browser');
    expect(kq.position).toEqual({ lat: 21.01, lng: 105.8 });
  });

  it('khong co trinh duyet thi dung dia chi da luu, va NOI RO la dia chi nao', () => {
    const kq = chonViTri(null, NHA);
    expect(kq.source).toBe('saved');
    expect(kq.position).toEqual({ lat: NHA.lat, lng: NHA.lng });
    expect(kq.label).toContain('Nhà');
  });

  it('khong co gi thi ve trung tam Ha Noi', () => {
    const kq = chonViTri(null, null);
    expect(kq.source).toBe('center');
    expect(kq.position).toEqual(HANOI_CENTER);
    expect(kq.label).toBe('Trung tâm Hà Nội');
  });
});

describe('useUserLocation', () => {
  it('khach (chua dang nhap): trung tam Ha Noi, KHONG goi /me/addresses', () => {
    const fetchGia = gia_lap_fetch([]);
    vi.stubGlobal('fetch', fetchGia);
    const { result } = renderHook(() => useUserLocation(), { wrapper });
    expect(result.current.source).toBe('center');
    expect(result.current.isDefault).toBe(true);
    expect(fetchGia.mock.calls.some(([u]) => String(u).includes('/me/addresses'))).toBe(false);
  });

  it('da dang nhap + co dia chi mac dinh: dung dia chi do, nhan noi ro', async () => {
    sessionStorage.setItem('moodbite.user.token', 'token-gia-lap');
    vi.stubGlobal(
      'fetch',
      gia_lap_fetch([
        { address_id: 'a2', label: 'Công ty', address_text: null, lat: 21.0, lng: 105.8, is_default: false },
        { address_id: 'a1', label: 'Nhà', address_text: null, lat: NHA.lat, lng: NHA.lng, is_default: true },
      ]),
    );
    const { result } = renderHook(() => useUserLocation(), { wrapper });

    await waitFor(() => expect(result.current.source).toBe('saved'));
    expect(result.current.position).toEqual({ lat: NHA.lat, lng: NHA.lng });
    expect(result.current.label).toBe('Địa chỉ đã lưu: Nhà');
    // Địa chỉ đã lưu là một chỗ THẬT người dùng chọn -> không phải "mặc định Hồ Gươm".
    expect(result.current.isDefault).toBe(false);
  });

  it('bi tu choi dinh vi: cau loi noi DANG DUNG DIA CHI DA LUU', async () => {
    sessionStorage.setItem('moodbite.user.token', 'token-gia-lap');
    vi.stubGlobal(
      'fetch',
      gia_lap_fetch([
        { address_id: 'a1', label: 'Nhà', address_text: null, lat: NHA.lat, lng: NHA.lng, is_default: true },
      ]),
    );
    tu_choi_dinh_vi();
    const { result } = renderHook(() => useUserLocation(), { wrapper });
    await waitFor(() => expect(result.current.source).toBe('saved'));

    act(() => result.current.request());

    expect(result.current.error).toBe(
      'Bạn đã từ chối chia sẻ vị trí. Đang dùng địa chỉ đã lưu "Nhà".',
    );
    expect(result.current.source).toBe('saved');
  });

  it('co dia chi nhung KHONG co cai nao mac dinh: van ve trung tam Ha Noi', async () => {
    sessionStorage.setItem('moodbite.user.token', 'token-gia-lap');
    const fetchGia = gia_lap_fetch([
      { address_id: 'a1', label: 'Nhà', address_text: null, lat: NHA.lat, lng: NHA.lng, is_default: false },
    ]);
    vi.stubGlobal('fetch', fetchGia);
    tu_choi_dinh_vi();
    const { result } = renderHook(() => useUserLocation(), { wrapper });
    await waitFor(() =>
      expect(fetchGia.mock.calls.some(([u]) => String(u).includes('/me/addresses'))).toBe(true),
    );
    act(() => result.current.request());
    expect(result.current.source).toBe('center');
    expect(result.current.error).toBe(
      'Bạn đã từ chối chia sẻ vị trí. Đang dùng trung tâm Hà Nội.',
    );
  });
});
