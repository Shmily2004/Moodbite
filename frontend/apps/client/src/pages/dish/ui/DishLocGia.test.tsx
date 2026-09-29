/**
 * Trang chi tiết món: công tắc "chỉ quán có ghi giá" phải đổi DANH SÁCH QUÁN NGAY TẠI CHỖ.
 *
 * Khác mọi ô lọc còn lại trong cùng ngăn kéo (chúng đợi nút "Xem kết quả" rồi sang
 * `/recommend`), vì trang này đã khoá vào một món: thứ người dùng vừa lọc đang nằm ngay
 * dưới tay họ. Xem `useDishFilterPanel` để biết lý do đầy đủ.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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
  restaurant_count: 62,
  nearest_restaurant_km: 0.9,
  rank_position: 1,
  score: 0.8,
  reasons: [],
  source: 'manual',
  source_url: null,
  data_confidence: 'manual',
};

/** Mọi URL đã gọi tới `/dishes/ga-ran/restaurants`. */
function theoDoiFetch(): string[] {
  const daGoi: string[] = [];
  vi.stubGlobal(
    'fetch',
    vi.fn().mockImplementation((url: string) => {
      const u = String(url);
      if (u.includes('/restaurants')) daGoi.push(u);
      const body = u.includes('/restaurants')
        ? { search_query_id: 'q1', results: [], context: [], warnings: [] }
        : MON;
      return Promise.resolve({ ok: true, status: 200, json: async () => ({ data: body }) });
    }),
  );
  return daGoi;
}

function renderDish() {
  return render(
    <MemoryRouter initialEntries={['/dishes/ga-ran']}>
      <UserSessionProvider>
        <Routes>
          <Route path="/dishes/:dishId" element={<DishPage />} />
        </Routes>
      </UserSessionProvider>
    </MemoryRouter>,
  );
}

describe('Trang món - công tắc giá áp tại chỗ', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  afterEach(() => vi.unstubAllGlobals());

  it('mặc định gọi API với only_with_price=false', async () => {
    const daGoi = theoDoiFetch();
    renderDish();

    await waitFor(() => expect(daGoi.length).toBeGreaterThan(0));
    expect(daGoi[0]).toContain('only_with_price=false');
  });

  it('tick công tắc -> GỌI LẠI API ngay, không phải chờ bấm "Xem kết quả"', async () => {
    const daGoi = theoDoiFetch();
    renderDish();

    await waitFor(() => expect(daGoi.length).toBeGreaterThan(0));
    const truoc = daGoi.length;

    fireEvent.click(await screen.findByRole('button', { name: /Chỉnh sửa/i }));
    fireEvent.click(await screen.findByLabelText(/Chỉ hiện quán có ghi giá/i));

    await waitFor(() => expect(daGoi.length).toBeGreaterThan(truoc));
    expect(daGoi[daGoi.length - 1]).toContain('only_with_price=true');
  });
});
