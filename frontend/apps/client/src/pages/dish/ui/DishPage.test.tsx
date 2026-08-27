/**
 * TRANG CHI TIẾT MÓN — khoá lại phần dựng theo `design/restaurance recommend.png`
 * (chủ dự án chốt 2026-08-27).
 *
 * Giả lập `fetch` ở mức thấp nhất để đi qua ĐÚNG lớp `HttpClient` thật: đọc sai tên
 * trường (`is_famous`, `distance_m`…) là test đỏ ngay.
 */
import { describe, expect, it, vi, afterEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { DishPage } from '../index';

/** Bản đồ Leaflet không dựng được trong jsdom — thay bằng ô trống có nhãn nhận biết. */
vi.mock('@/widgets/restaurant-map', () => ({
  RestaurantMap: () => <div data-testid="ban-do" />,
}));

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
  restaurant_count: 20,
  source: 'manual',
  source_url: null,
};

function quan(i: number, extra: Record<string, unknown> = {}) {
  return {
    restaurant_id: `q${i}`,
    name: `Quán số ${i}`,
    category: 'Quán ăn',
    address: `${i} Lê Duẩn`,
    latitude: 21.02 + i / 1000,
    longitude: 105.85,
    distance_m: i * 100,
    price_range: null,
    rating: null,
    user_ratings_total: null,
    is_famous: false,
    rank_position: i,
    predicted_score: 0.6,
    match_source: 'name',
    thumbnail_url: null,
    district: 'Hoàn Kiếm',
    dietary: [],
    amenities: [],
    source: 'osm',
    experience_cluster_id: null,
    experience_cluster_label: null,
    temporarily_closed: null,
    source_updated_at: null,
    source_datasets: [],
    surveyed_at: null,
    suggested_dish: null,
    ...extra,
  };
}

function mockApi(quanList: unknown[]) {
  return vi.fn().mockImplementation((url: string) => {
    const s = String(url);
    const data = s.includes('/restaurants')
      ? { search_query_id: 'q1', results: quanList, context: [], warnings: [] }
      : MON;
    return Promise.resolve({ ok: true, status: 200, json: async () => ({ data }) });
  });
}

function renderTrang() {
  return render(
    <MemoryRouter initialEntries={['/dishes/bun-cha']}>
      <Routes>
        <Route path="/dishes/:dishId" element={<DishPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('DishPage — theo bản thiết kế', () => {
  it('thẻ quán có SỐ THỨ TỰ để khớp với ghim bản đồ', async () => {
    vi.stubGlobal('fetch', mockApi([quan(1), quan(2), quan(3)]));
    const { container } = renderTrang();

    await screen.findByText('Quán số 1');

    // Số nằm trên ảnh quán. Không có nó thì 20 ghim trên bản đồ giống hệt nhau và
    // không nối được với danh sách.
    const so = [...container.querySelectorAll('.card__so')].map((n) => n.textContent);
    expect(so).toEqual(['1', '2', '3']);
  });

  it('mỗi thẻ có ĐÚNG MỘT nút "Xem chi tiết"', async () => {
    vi.stubGlobal('fetch', mockApi([quan(1), quan(2)]));
    const { container } = renderTrang();

    await screen.findByText('Quán số 1');

    // Đếm theo class thay vì theo vai trò: `RestaurantList` còn có panel chi tiết bên
    // trong cũng dùng chữ tương tự, nên đếm theo tên nút sẽ lẫn.
    expect(container.querySelectorAll('.card__xem')).toHaveLength(2);
  });

  it('nhãn "Nổi tiếng" chỉ hiện khi backend nói vậy', async () => {
    // ⚠️ Quy tắc ở `domain/services/restaurant_badges.py` — frontend KHÔNG tự tính.
    vi.stubGlobal(
      'fetch',
      mockApi([quan(1, { is_famous: true }), quan(2, { is_famous: false })]),
    );
    const { container } = renderTrang();

    await screen.findByText('Quán số 1');
    expect(container.querySelectorAll('.card__noi-tieng')).toHaveLength(1);
  });

  it('cắt bớt danh sách và có nút "Xem thêm N quán"', async () => {
    // 12 quán > SO_QUAN_BAN_DAU (8). 20 thẻ đẩy bản đồ ra khỏi màn hình ngay lần đầu vào.
    vi.stubGlobal('fetch', mockApi(Array.from({ length: 12 }, (_, i) => quan(i + 1))));
    renderTrang();

    await screen.findByText('Quán số 1');
    expect(screen.queryByText('Quán số 12')).not.toBeInTheDocument();

    // Nói rõ CÒN BAO NHIÊU, không chỉ ghi "xem thêm".
    const nut = screen.getByRole('button', { name: /Xem thêm 4 quán/ });
    fireEvent.click(nut);

    await waitFor(() => expect(screen.getByText('Quán số 12')).toBeInTheDocument());
  });

  it('ít quán thì KHÔNG hiện nút "Xem thêm"', async () => {
    vi.stubGlobal('fetch', mockApi([quan(1), quan(2)]));
    renderTrang();

    await screen.findByText('Quán số 1');
    expect(screen.queryByRole('button', { name: /Xem thêm/ })).not.toBeInTheDocument();
  });

  it('"Xem danh sách" thu bản đồ, và hiện lại được', async () => {
    vi.stubGlobal('fetch', mockApi([quan(1)]));
    renderTrang();

    await screen.findByText('Quán số 1');
    expect(screen.getByTestId('ban-do')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Xem danh sách/ }));
    expect(screen.queryByTestId('ban-do')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Hiện lại bản đồ/ }));
    expect(screen.getByTestId('ban-do')).toBeInTheDocument();
  });

  it('nút "Chỉnh sửa" mở ngăn kéo bộ lọc ngay tại trang', async () => {
    vi.stubGlobal('fetch', mockApi([quan(1)]));
    renderTrang();

    fireEvent.click(await screen.findByRole('button', { name: /Chỉnh sửa/ }));

    // Không rời trang: tên món vẫn còn.
    expect(screen.getByText(/Đổi tiêu chí sẽ đưa bạn về trang gợi ý món/)).toBeInTheDocument();
  });
});
