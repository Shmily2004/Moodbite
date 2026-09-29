/**
 * Công tắc "Chỉ hiện quán có ghi giá" phải đi tới được backend.
 *
 * Kiểm ở mức DOM + `fetch` thật vì phần dễ hỏng nhất không phải state, mà là đoạn dây từ
 * ô tick -> props -> body gửi lên. Trước khi có tham số này, API gợi ý món không có cách
 * nào lọc theo giá, nên bản vẽ `Filler.png` không dựng được.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { UserSessionProvider } from '@/entities/user';
import { HomePage } from '../index';

const MON = {
  dish_id: 'bun-cha',
  name: 'Bún chả',
  cuisine: 'Việt Nam',
  spice_level: 1,
  temperature: 'hot',
  cooking_method: 'nuong',
  meal_times: ['trua'],
  has_description: true,
  description: 'Bún chả là món Hà Nội.',
  image_url: null,
  restaurant_count: 86,
  nearest_restaurant_km: 0.6,
  rank_position: 1,
  score: 0.81,
  reasons: [],
  source: 'manual',
  source_url: null,
  data_confidence: 'manual',
};

function theoDoiFetch(): Record<string, unknown>[] {
  const daGui: Record<string, unknown>[] = [];
  vi.stubGlobal(
    'fetch',
    vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (String(url).includes('/dishes/suggest') && init?.body) {
        daGui.push(JSON.parse(String(init.body)));
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => ({
          data: { search_query_id: 'q1', results: [MON], context: [], warnings: [] },
        }),
      });
    }),
  );
  return daGui;
}

function renderHome() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <UserSessionProvider>
        <HomePage />
      </UserSessionProvider>
    </MemoryRouter>,
  );
}

describe('Công tắc "chỉ quán có ghi giá"', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  afterEach(() => vi.unstubAllGlobals());

  it('mặc định TẮT - đây là thay đổi cộng thêm, không đổi hành vi cũ', async () => {
    const daGui = theoDoiFetch();
    renderHome();

    await waitFor(() => expect(daGui.length).toBeGreaterThan(0));
    expect(daGui[0].only_with_price).toBe(false);
  });

  it('tick vào thì lượt gọi sau gửi `only_with_price: true`', async () => {
    const daGui = theoDoiFetch();
    renderHome();

    fireEvent.click(await screen.findByRole('button', { name: /Lọc/i }));
    fireEvent.click(await screen.findByLabelText(/Chỉ hiện quán có ghi giá/i));

    await waitFor(() => expect(daGui.length).toBeGreaterThan(1));
    expect(daGui[daGui.length - 1].only_with_price).toBe(true);
  });

  it('nói rõ cái giá phải trả ngay cạnh công tắc', async () => {
    theoDoiFetch();
    renderHome();

    fireEvent.click(await screen.findByRole('button', { name: /Lọc/i }));

    // Người dùng phải biết TRƯỚC khi bật rằng kết quả sẽ ít đi vì DỮ LIỆU thiếu, không
    // phải vì khu vực ít quán.
    expect(await screen.findByText(/chưa có giá/i)).toBeInTheDocument();
  });
});
