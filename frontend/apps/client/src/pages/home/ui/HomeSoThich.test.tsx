/**
 * SỞ THÍCH ĐÃ LƯU phải thật sự đi vào lượt gọi API của trang chủ.
 *
 * Test này đọc THẲNG body gửi lên `fetch`, không mock `@/shared/api`: thứ cần chứng minh
 * là lời hứa "MoodBite sẽ bật sẵn các bộ lọc này" có tới được backend hay không. Một bài
 * test dừng ở mức "hook trả về đúng object" sẽ vẫn xanh kể cả khi không ai gửi nó đi —
 * mà đó chính là trạng thái của tính năng này trước ngày 2026-09-23.
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
  description: 'Bún chả là món Hà Nội gồm chả thịt lợn nướng than.',
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

/** Mọi body đã gửi lên `/dishes/suggest`, theo đúng thứ tự. */
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

describe('Trang chủ áp sở thích đã lưu', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  afterEach(() => vi.unstubAllGlobals());

  it('chưa lưu sở thích nào thì KHÔNG tự lọc gì và không nói gì', async () => {
    const daGui = theoDoiFetch();
    renderHome();

    await waitFor(() => expect(daGui.length).toBeGreaterThan(0));
    expect(daGui[0].cooking_methods).toEqual([]);
    expect(daGui[0].mood).toBeNull();
    expect(screen.queryByText(/Đã bật sẵn/i)).not.toBeInTheDocument();
  });

  it('sở thích đã lưu ĐI ĐƯỢC vào body gửi lên /dishes/suggest', async () => {
    localStorage.setItem('moodbite.taste', JSON.stringify(['nuong', 'cay']));
    const daGui = theoDoiFetch();
    renderHome();

    await waitFor(() => expect(daGui.length).toBeGreaterThan(0));
    // Đây là vế từng hỏng: bản cũ nạp sở thích trong `useEffect` nên lần dựng đầu tiên
    // luôn gửi lên mảng rỗng, và `useDishFilterState` chỉ đọc giá trị khởi tạo một lần.
    expect(daGui[0].cooking_methods).toEqual(['nuong']);
    expect(daGui[0].mood).toBe('excited');
  });

  it('NÓI RA là đã tự bật bộ lọc, kèm số lượng', async () => {
    localStorage.setItem('moodbite.taste', JSON.stringify(['nuong', 'cay']));
    theoDoiFetch();
    renderHome();

    // Im lặng lọc hộ người dùng là đúng lỗi CLAUDE.md mục 5 cấm.
    expect(await screen.findByText(/Đã bật sẵn 2 bộ lọc/i)).toBeInTheDocument();
  });

  it('bỏ lọc theo sở thích thì lượt gọi SAU không còn bộ lọc đó', async () => {
    localStorage.setItem('moodbite.taste', JSON.stringify(['nuong']));
    const daGui = theoDoiFetch();
    renderHome();

    await waitFor(() => expect(daGui[0].cooking_methods).toEqual(['nuong']));
    fireEvent.click(await screen.findByRole('button', { name: /Bỏ lọc theo sở thích/i }));

    await waitFor(() => expect(daGui.length).toBeGreaterThan(1));
    expect(daGui[daGui.length - 1].cooking_methods).toEqual([]);
  });

  it('bỏ lọc xong thì câu thông báo biến mất - không để lại lời nói sai', async () => {
    localStorage.setItem('moodbite.taste', JSON.stringify(['nuong']));
    theoDoiFetch();
    renderHome();

    fireEvent.click(await screen.findByRole('button', { name: /Bỏ lọc theo sở thích/i }));

    await waitFor(() =>
      expect(screen.queryByText(/Đã bật sẵn/i)).not.toBeInTheDocument(),
    );
  });
});
