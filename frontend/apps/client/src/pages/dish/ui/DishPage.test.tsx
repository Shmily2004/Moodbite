/**
 * TRANG CHI TIẾT MÓN — khoá lại phần dựng theo `design/restaurance recommend.png`
 * (chủ dự án chốt 2026-08-27).
 *
 * Giả lập `fetch` ở mức thấp nhất để đi qua ĐÚNG lớp `HttpClient` thật: đọc sai tên
 * trường (`is_famous`, `distance_m`…) là test đỏ ngay.
 */
import { describe, expect, it, vi, afterEach } from 'vitest';
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import type { NavigateFunction } from 'react-router-dom';
import { UserSessionProvider } from '@/entities/user';
import { LanguageProvider } from '@/shared/i18n';
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
    // Món đã bị gỡ khỏi danh mục -> đúng envelope lỗi 404 mà backend trả.
    if (s.includes('mon-da-go')) {
      return Promise.resolve({
        ok: false,
        status: 404,
        json: async () => ({
          error: { code: 'DISH_NOT_FOUND', message: 'Không tìm thấy món', details: {} },
        }),
      });
    }
    const data = s.includes('/restaurants')
      ? { search_query_id: 'q1', results: quanList, context: [], warnings: [] }
      : MON;
    return Promise.resolve({ ok: true, status: 200, json: async () => ({ data }) });
  });
}

/** Lộ `navigate` ra ngoài để test đổi `:dishId` mà KHÔNG gỡ `DishPage` khỏi cây. */
let dieuHuong: NavigateFunction = () => undefined;
function LayNavigate() {
  dieuHuong = useNavigate();
  return null;
}

/** Trang `/recommend` giả: chỉ in ra query string nhận được. */
function TrangGoiYGia() {
  const { search } = useLocation();
  return <p data-testid="recommend-search">{search}</p>;
}

function renderTrang(duongDan = '/dishes/bun-cha') {
  // `SiteHeader` đọc phiên đăng nhập + từ điển -> bọc provider y như `RootLayout`.
  return render(
    <MemoryRouter initialEntries={[duongDan]}>
      <LanguageProvider>
        <UserSessionProvider>
          <LayNavigate />
          <Routes>
            <Route path="/dishes/:dishId" element={<DishPage />} />
            <Route path="/recommend" element={<TrangGoiYGia />} />
          </Routes>
        </UserSessionProvider>
      </LanguageProvider>
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

  it('mức cay vẽ bằng icon quả ớt SVG KÈM CHỮ hiện ra (A9 + 2026-10-02)', async () => {
    // `spice_level: 1` -> một quả ớt. Trước 2026-09-29 đây là emoji 🌶️. Từ 2026-10-02
    // nhãn "Độ cay 1/3" hiện bằng chữ luôn: một quả ớt mảnh đứng riêng trông như chip rỗng.
    vi.stubGlobal('fetch', mockApi([quan(1)]));
    renderTrang();

    const cay = (await screen.findByText('Độ cay 1/3')).closest('li')!;
    expect(cay.querySelectorAll('svg')).toHaveLength(1);
    expect(cay.querySelector('svg')).toHaveAttribute('aria-hidden', 'true');
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

  it('dùng thanh trên CHUNG (SiteHeader) và vẫn giữ đường dẫn phân cấp', async () => {
    vi.stubGlobal('fetch', mockApi([quan(1)]));
    const { container } = renderTrang();

    await screen.findByText('Quán số 1');
    expect(container.querySelector('.site-header')).not.toBeNull();
    expect(screen.getByRole('navigation', { name: 'Đường dẫn' })).toBeInTheDocument();
  });

  it('nút "Chỉnh sửa" mở ngăn kéo bộ lọc ngay tại trang', async () => {
    vi.stubGlobal('fetch', mockApi([quan(1)]));
    renderTrang();

    fireEvent.click(await screen.findByRole('button', { name: /Chỉnh sửa/ }));

    // Không rời trang: câu giải thích của ngăn kéo hiện ra.
    expect(screen.getByText(/Đổi tiêu chí sẽ đưa bạn về trang gợi ý món/)).toBeInTheDocument();
  });

  it('ngăn kéo KHÔNG rỗng: có bộ lọc thật, bật sẵn thuộc tính của món', async () => {
    // Lỗi thật 2026-09-16: ngăn kéo chỉ có một câu chữ, không có ô lọc nào.
    vi.stubGlobal('fetch', mockApi([quan(1)]));
    renderTrang();

    fireEvent.click(await screen.findByRole('button', { name: /Chỉnh sửa/ }));
    const hopThoai = screen.getByRole('dialog');

    // Bún chả: `temperature: hot`, `cooking_method: nuong` -> hai ô này bật sẵn.
    const nut = (ten: RegExp) => within(hopThoai).getByRole('button', { name: ten });
    expect(nut(/Đồ nóng/)).toHaveAttribute('aria-pressed', 'true');
    expect(nut(/Đồ nướng/)).toHaveAttribute('aria-pressed', 'true');
    expect(nut(/Trời mưa/)).toHaveAttribute('aria-pressed', 'false');
    // Thanh trượt bán kính thay cho ô chọn cũ.
    expect(within(hopThoai).getByRole('slider')).toBeInTheDocument();
  });

  it('bộ lọc trên URL thắng thuộc tính của món', async () => {
    // Đi từ `/recommend?thoi_tiet=rain` sang: người dùng đã chọn "trời mưa", không chọn
    // "đồ nướng" — không được tự bật thêm thứ họ chưa chọn.
    vi.stubGlobal('fetch', mockApi([quan(1)]));
    renderTrang('/dishes/bun-cha?thoi_tiet=rain&km=3');

    fireEvent.click(await screen.findByRole('button', { name: /Chỉnh sửa/ }));
    const hopThoai = screen.getByRole('dialog');

    const nut = (ten: RegExp) => within(hopThoai).getByRole('button', { name: ten });
    expect(nut(/Trời mưa/)).toHaveAttribute('aria-pressed', 'true');
    expect(nut(/Đồ nướng/)).toHaveAttribute('aria-pressed', 'false');
    expect(within(hopThoai).getByText('3 km', { selector: 'strong' })).toBeInTheDocument();
  });

  it('"Xem kết quả" sang /recommend MANG THEO bộ lọc đã chọn', async () => {
    // Lỗi thật 2026-09-16: nút này nhảy sang `/recommend` trắng trơn.
    vi.stubGlobal('fetch', mockApi([quan(1)]));
    renderTrang();

    fireEvent.click(await screen.findByRole('button', { name: /Chỉnh sửa/ }));
    const hopThoai = screen.getByRole('dialog');
    fireEvent.click(within(hopThoai).getByRole('button', { name: /Bữa tối/ }));
    fireEvent.click(within(hopThoai).getByRole('button', { name: /Xem kết quả/ }));

    const search = await screen.findByTestId('recommend-search');
    const params = new URLSearchParams(search.textContent ?? '');
    // Đúng tên tham số mà `docBoLocTuUrl` ở trang `/recommend` đọc.
    expect(params.get('nhiet')).toBe('hot');
    expect(params.get('cach')).toBe('nuong');
    expect(params.get('bua')).toBe('toi');
  });

  it('đổi sang món ĐÃ BỊ GỠ (notFound) rồi quay lại KHÔNG sập trang', async () => {
    // Lỗi thật 2026-09-16 (Rules of Hooks): `useMemo` đứng sau `return` sớm, nên số hook
    // đổi giữa hai lần render -> "Rendered fewer hooks than expected".
    vi.stubGlobal('fetch', mockApi([quan(1)]));
    renderTrang();
    await screen.findByText('Quán số 1');

    act(() => {
      dieuHuong('/dishes/mon-da-go');
    });
    expect(await screen.findByText('Không tìm thấy món này')).toBeInTheDocument();

    act(() => {
      dieuHuong('/dishes/bun-cha');
    });
    expect(await screen.findByText('Quán số 1')).toBeInTheDocument();
    expect(screen.queryByText('Không tìm thấy món này')).not.toBeInTheDocument();
  });
});

describe('DishPage — tiêu đề danh sách nói thật số quán đang hiện (2026-10-02)', () => {
  it('chỉ hiện một phần thì tiêu đề phải là "Hiện x / tổng", không ngụ ý đã liệt kê hết', async () => {
    // Món đếm được 20 quán, API trả về 12, trang hiện trước 8.
    vi.stubGlobal('fetch', mockApi(Array.from({ length: 12 }, (_, i) => quan(i + 1))));
    renderTrang();

    expect(
      await screen.findByRole('heading', { level: 2, name: /Hiện 8 \/ 20 quán phù hợp với Bún chả/ }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Xem thêm 4 quán/ }));
    expect(
      await screen.findByRole('heading', { level: 2, name: /Hiện 12 \/ 20 quán/ }),
    ).toBeInTheDocument();
  });

  it('thẻ gọn: KHÔNG lặp "#1" cạnh tên, nhưng VẪN giữ mức tin cậy món và "chưa có đánh giá"', async () => {
    vi.stubGlobal(
      'fetch',
      mockApi([
        quan(1, { suggested_dish: { name: 'Bún chả', confidence: 'generic_fallback' } }),
      ]),
    );
    const { container } = renderTrang();

    await screen.findByText('Quán số 1');
    expect(container.querySelector('.card__rank')).toBeNull();
    // Số thứ tự vẫn nằm trên ảnh, khớp ghim bản đồ.
    expect(container.querySelector('.card__so')?.textContent).toBe('1');
    expect(screen.getByText('chưa có đánh giá')).toBeInTheDocument();
    expect(screen.getByText(/Khớp tên quán/i)).toBeInTheDocument();
    expect(container.querySelector('.card__chip--guess')).not.toBeNull();
  });
});
