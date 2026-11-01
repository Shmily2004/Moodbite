/**
 * TRANG CHI TIẾT QUÁN (2026-10-28). Giả lập `fetch` ở mức thấp nhất để đi qua đúng lớp
 * `HttpClient` thật - đọc sai tên trường của `info` là test đỏ ngay.
 *
 * Khoá những luật trung thực của dự án (CLAUDE.md mục 4) trên trang mới:
 *   - thiếu rating -> "chưa có đánh giá", không bao giờ "0"
 *   - quán chưa có review/ảnh là chuyện BÌNH THƯỜNG, phải nói rõ thay vì để trống
 *   - review chỉ có số sao (text null) không được thành thẻ rỗng
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { UserSessionProvider } from '@/entities/user';
import { LanguageProvider } from '@/shared/i18n';
import { RestaurantPage } from '../index';

/** Leaflet không dựng được trong jsdom - thay bằng ô trống có nhãn nhận biết. */
vi.mock('./RestaurantLocationMap', () => ({
  RestaurantLocationMap: () => <div data-testid="ban-do" />,
}));

const INFO = {
  name: 'Bún Chả Hương Liên',
  category: 'Quán bún chả',
  cuisine: null,
  address: '24 Lê Văn Hưu, Hai Bà Trưng',
  district: 'Phường Hai Bà Trưng',
  latitude: 21.0178,
  longitude: 105.8537,
  price_range: null,
  rating: null,
  user_ratings_total: null,
  is_famous: false,
  thumbnail_url: null,
  opening_hours: 'Mo-Su 08:00-22:00',
  phone: '+84 24 3943 4106',
  website: null,
  socials: [],
  atmosphere_tags: [],
  dietary: [],
  amenities: [],
  source: 'openstreetmap',
  data_confidence: 'medium',
  experience_cluster_label: null,
  temporarily_closed: null,
  source_updated_at: null,
  source_datasets: [],
  surveyed_at: null,
};

function chiTiet(extra: Record<string, unknown> = {}) {
  return {
    restaurant_id: 'q1',
    has_details: false,
    reason: 'Quán này lấy từ OpenStreetMap, chưa có dữ liệu giá/review/ảnh.',
    name: null,
    price_range: null,
    atmosphere: null,
    opening_hours: null,
    images: [],
    reviews: [],
    menu_url: null,
    website: null,
    google_maps_url: null,
    review_summary: null,
    info: INFO,
    ...extra,
  };
}

function mockApi(data: unknown, status = 200) {
  return vi.fn().mockImplementation((url: string) => {
    // Ghi tương tác: trả OK, test này không kiểm nội dung nhãn.
    if (String(url).includes('/interactions')) {
      return Promise.resolve({ ok: true, status: 201, json: async () => ({ data: {} }) });
    }
    if (status === 404) {
      return Promise.resolve({
        ok: false,
        status: 404,
        json: async () => ({
          error: { code: 'RESTAURANT_NOT_FOUND', message: 'Không tìm thấy quán', details: {} },
        }),
      });
    }
    return Promise.resolve({ ok: true, status: 200, json: async () => ({ data }) });
  });
}

function renderTrang(duongDan = '/restaurants/q1') {
  return render(
    <MemoryRouter initialEntries={[duongDan]}>
      <LanguageProvider>
        <UserSessionProvider>
          <Routes>
            <Route path="/restaurants/:restaurantId" element={<RestaurantPage />} />
          </Routes>
        </UserSessionProvider>
      </LanguageProvider>
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('RestaurantPage', () => {
  it('quán OSM chưa có chi tiết vẫn hiện tên, địa chỉ, giờ, bản đồ và nói rõ thiếu review', async () => {
    vi.stubGlobal('fetch', mockApi(chiTiet()));
    renderTrang();

    expect(await screen.findByRole('heading', { level: 1, name: /Bún Chả Hương Liên/ }))
      .toBeInTheDocument();
    expect(screen.getAllByText('24 Lê Văn Hưu, Hai Bà Trưng').length).toBeGreaterThan(0);
    expect(screen.getByText('Mo-Su 08:00-22:00')).toBeInTheDocument();
    expect(screen.getByTestId('ban-do')).toBeInTheDocument();
    expect(screen.getByText('Quán này chưa có ảnh và đánh giá')).toBeInTheDocument();
  });

  it('thiếu rating hiện "chưa có đánh giá", KHÔNG BAO GIỜ là 0', async () => {
    vi.stubGlobal('fetch', mockApi(chiTiet()));
    const { container } = renderTrang();
    await screen.findByRole('heading', { level: 1 });

    const chip = container.querySelector('.rest-hero .dish-attrs')!;
    expect(within(chip as HTMLElement).queryByText(/^0/)).toBeNull();
    expect(chip.textContent).toMatch(/Chưa có đánh giá/i);
  });

  it('chỉ đường luôn có link, dựng từ toạ độ khi không có trang Google Maps', async () => {
    vi.stubGlobal('fetch', mockApi(chiTiet()));
    renderTrang();
    const link = await screen.findByRole('link', { name: /Chỉ đường/ });
    expect(link.getAttribute('href')).toBe(
      'https://www.google.com/maps/dir/?api=1&destination=21.0178,105.8537',
    );
  });

  it('quán có chi tiết: hiện bảng giờ, ảnh, và BỎ review không có chữ', async () => {
    vi.stubGlobal(
      'fetch',
      mockApi(
        chiTiet({
          has_details: true,
          reason: null,
          opening_hours: [{ day: 'Thứ Hai', hours: '08:00 to 22:00' }],
          images: ['https://example.com/a.jpg'],
          google_maps_url: 'https://maps.google.com/?cid=1',
          reviews: [
            { name: 'A', text: null, stars: 5 },
            { name: 'B', text: 'Chả nướng thơm, nước chấm vừa.', stars: 4 },
          ],
        }),
      ),
    );
    renderTrang();

    expect(await screen.findByText('Chả nướng thơm, nước chấm vừa.')).toBeInTheDocument();
    // Một review có chữ -> tiêu đề đếm 1, không đếm review chỉ có sao.
    expect(screen.getByRole('heading', { name: /Đánh giá \(1\)/ })).toBeInTheDocument();
    expect(screen.getByText('08:00 to 22:00')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Chỉ đường/ }).getAttribute('href')).toBe(
      'https://maps.google.com/?cid=1',
    );
  });

  it('404 hiện trang "không tìm thấy quán" có đường về, không phải lỗi "thử lại"', async () => {
    vi.stubGlobal('fetch', mockApi(null, 404));
    renderTrang('/restaurants/khong-co');
    expect(await screen.findByText('Không tìm thấy quán này')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Về trang chủ' })).toBeInTheDocument();
  });

  it('link ảnh hết hạn: ảnh đầu trang lui về ô biểu tượng, thẻ "Ảnh quán" biến mất', async () => {
    // Lỗi thật thấy khi chụp màn hình 2026-10-28: cả 8 ảnh Google của một quán đều hỏng,
    // trang hiện khung ảnh trắng + thẻ "Ảnh quán (8)" rỗng.
    vi.stubGlobal(
      'fetch',
      mockApi(chiTiet({ has_details: true, reason: null, images: ['https://x/het-han.jpg'] })),
    );
    const { container } = renderTrang();
    await screen.findByRole('heading', { name: /Ảnh quán \(1\)/ });

    for (const img of container.querySelectorAll('img[src="https://x/het-han.jpg"]')) {
      fireEvent.error(img);
    }

    expect(screen.queryByRole('heading', { name: /Ảnh quán/ })).toBeNull();
    expect(container.querySelector('.rest-hero__anh .thumb--generated')).not.toBeNull();
  });
});
