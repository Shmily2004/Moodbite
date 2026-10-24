/**
 * Trang món phải dùng ĐÚNG bán kính người dùng đã chọn ở lưới món (`?km=` trên URL).
 *
 * BUG THẬT (2026-10-13): `/recommend` ghi `km` lên URL khi mở món, nhưng trang món bỏ qua
 * và luôn gọi API với 10 km. Chọn 1 km thì thẻ món hứa "2 quán", bấm vào thì danh sách
 * đếm trong 10 km. Chọn "Không giới hạn" (`km=`) cũng thành 10 km.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { UserSessionProvider } from '@/entities/user';
import { DishPage } from '../index';

const MON = {
  dish_id: 'ga-ran',
  name: 'Gà rán',
  cuisine: null,
  spice_level: null,
  temperature: 'hot',
  cooking_method: 'chien',
  meal_times: [],
  has_description: true,
  description: 'Gà rán là thịt gà tẩm bột chiên giòn.',
  image_url: null,
  restaurant_count: 2,
  nearest_restaurant_km: 0.4,
  rank_position: 1,
  score: 0.8,
  reasons: [],
  source: 'manual',
  source_url: null,
  data_confidence: 'manual',
};

/** Mọi URL đã gọi tới API của món (cả chi tiết lẫn danh sách quán). */
function theoDoiFetch(): string[] {
  const daGoi: string[] = [];
  vi.stubGlobal(
    'fetch',
    vi.fn().mockImplementation((url: string) => {
      const u = String(url);
      daGoi.push(u);
      const body = u.includes('/restaurants')
        ? { search_query_id: 'q1', results: [], context: [], warnings: [] }
        : MON;
      return Promise.resolve({ ok: true, status: 200, json: async () => ({ data: body }) });
    }),
  );
  return daGoi;
}

function renderDish(url: string) {
  return render(
    <MemoryRouter initialEntries={[url]}>
      <UserSessionProvider>
        <Routes>
          <Route path="/dishes/:dishId" element={<DishPage />} />
        </Routes>
      </UserSessionProvider>
    </MemoryRouter>,
  );
}

/** Đợi CẢ HAI lượt gọi (chi tiết + danh sách quán) rồi trả về đúng hai URL đó. */
async function haiLuotGoi(daGoi: string[]) {
  await waitFor(() => {
    expect(daGoi.some((u) => u.includes('/dishes/ga-ran/restaurants'))).toBe(true);
    expect(daGoi.some((u) => /\/dishes\/ga-ran\?/.test(u))).toBe(true);
  });
  return daGoi.filter((u) => u.includes('/dishes/ga-ran'));
}

describe('Trang món - bán kính theo từ lưới món sang', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  afterEach(() => vi.unstubAllGlobals());

  it('?km=1 -> CẢ HAI lượt gọi dùng 1 km', async () => {
    const daGoi = theoDoiFetch();
    renderDish('/dishes/ga-ran?km=1');

    for (const u of await haiLuotGoi(daGoi)) {
      expect(u).toMatch(/max_distance_km=1(&|$)/);
      expect(u).not.toContain('no_distance_limit');
    }
  });

  it('?km= (Không giới hạn) -> gửi no_distance_limit, không gửi 10 km', async () => {
    const daGoi = theoDoiFetch();
    renderDish('/dishes/ga-ran?km=');

    for (const u of await haiLuotGoi(daGoi)) {
      expect(u).toContain('no_distance_limit=true');
      expect(u).not.toContain('max_distance_km');
    }
  });

  it('không có km (mở từ trang chủ / link chia sẻ) -> mặc định 10 km như cũ', async () => {
    const daGoi = theoDoiFetch();
    renderDish('/dishes/ga-ran');

    for (const u of await haiLuotGoi(daGoi)) {
      expect(u).toMatch(/max_distance_km=10(&|$)/);
    }
  });

  it('?km=abc (hỏng) -> bỏ qua, dùng mặc định, KHÔNG thành không giới hạn', async () => {
    const daGoi = theoDoiFetch();
    renderDish('/dishes/ga-ran?km=abc');

    for (const u of await haiLuotGoi(daGoi)) {
      expect(u).toMatch(/max_distance_km=10(&|$)/);
      expect(u).not.toContain('no_distance_limit');
    }
  });
});
