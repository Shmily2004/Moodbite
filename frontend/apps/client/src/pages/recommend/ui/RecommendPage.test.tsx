/**
 * Trang KẾT QUẢ GỢI Ý MÓN.
 *
 * Thứ đáng khoá nhất ở đây là BỘ LỌC ĐI QUA URL — vì nó là lý do trang này tách ra được
 * khỏi trang chủ. Sai một tên tham số là đường dẫn đã chia sẻ không còn lọc đúng nữa,
 * mà không có gì báo lỗi.
 */
import { describe, expect, it, vi, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { UserSessionProvider } from '@/entities/user';
import { RecommendPage } from '../index';
import { docBoLocTuUrl, ghiBoLocLenUrl } from '@/features/suggest-dishes';
import { EMPTY_FILTERS } from '@/features/suggest-dishes';

function mockOk(dishes: unknown[]) {
  return vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({
      data: { search_query_id: 'q1', results: dishes, context: ['buổi tối'], warnings: [] },
    }),
  });
}

const MON = {
  dish_id: 'bun-cha',
  name: 'Bún chả',
  restaurant_count: 426,
  rank_position: 1,
  score: 0.7,
  reasons: [],
  meal_times: [],
  has_description: false,
  is_category: false,
};

function renderTrang(duongDan = '/recommend') {
  // `SiteHeader` bên trong trang đọc phiên đăng nhập -> phải bọc provider, đúng như
  // `RootLayout` làm lúc chạy thật.
  return render(
    <MemoryRouter initialEntries={[duongDan]}>
      <UserSessionProvider>
        <RecommendPage />
      </UserSessionProvider>
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('boLocTuUrl', () => {
  it('đọc rồi ghi lại cho ra ĐÚNG bộ lọc ban đầu', () => {
    // Vòng tròn đọc-ghi phải khép kín, nếu không thì mỗi lần chuyển trang bộ lọc lại
    // rơi mất một phần mà người dùng không hiểu vì sao.
    const goc = {
      ...EMPTY_FILTERS,
      cookingMethods: ['nuong', 'nuoc'],
      mealTimes: ['toi'],
      mood: 'relaxed',
      weather: 'rain',
      maxDistanceKm: 3,
    };

    const doc_lai = docBoLocTuUrl(ghiBoLocLenUrl(goc));

    expect({ ...EMPTY_FILTERS, ...doc_lai }).toEqual(goc);
  });

  it('phân biệt "không giới hạn bán kính" với "chưa chọn gì"', () => {
    // `km=` (rỗng) = người dùng CHỌN không giới hạn -> null.
    // Không có tham số `km` = chưa chọn -> để mặc định, KHÔNG được thành null.
    expect(docBoLocTuUrl(new URLSearchParams('km=')).maxDistanceKm).toBeNull();
    expect(docBoLocTuUrl(new URLSearchParams('')).maxDistanceKm).toBeUndefined();
  });

  it('bỏ giá trị rỗng khi tách chuỗi', () => {
    // "nuong,,nuoc" mà giữ nguyên thì backend nhận một mã lọc rỗng và trả 400.
    expect(docBoLocTuUrl(new URLSearchParams('cach=nuong,,nuoc')).cookingMethods).toEqual([
      'nuong',
      'nuoc',
    ]);
  });
});

describe('RecommendPage', () => {
  it('gửi bộ lọc đọc từ URL lên API', async () => {
    const fetchMock = mockOk([MON]);
    vi.stubGlobal('fetch', fetchMock);

    renderTrang('/recommend?mood=relaxed&thoi_tiet=rain&bua=toi&km=3');

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const body = JSON.parse(String(fetchMock.mock.calls[0][1].body));
    expect(body.mood).toBe('relaxed');
    expect(body.weather).toBe('rain');
    expect(body.meal_times).toEqual(['toi']);
    expect(body.max_distance_km).toBe(3);
  });

  it('KHÔNG xin danh mục — lưới chỉ hiện món cụ thể', async () => {
    // "Bún" là danh mục, không phải món để gợi ý. Xem `Dish.is_category`.
    const fetchMock = mockOk([MON]);
    vi.stubGlobal('fetch', fetchMock);

    renderTrang();

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(JSON.parse(String(fetchMock.mock.calls[0][1].body)).only_categories).toBe(false);
  });

  it('hiện tiêu đề và khối "phù hợp nhất" theo thiết kế', async () => {
    // Thiết kế `Food recommend.jpg` bỏ dòng "N món phù hợp", thay bằng tiêu đề cố định
    // và các khối có nhãn riêng.
    vi.stubGlobal('fetch', mockOk([MON]));

    renderTrang();

    expect(await screen.findByText(/Món phù hợp với bạn hôm nay/)).toBeInTheDocument();
    expect(screen.getByText(/Những món phù hợp nhất/i)).toBeInTheDocument();
  });

  it('chip bộ lọc đang bật gỡ được từng cái', async () => {
    vi.stubGlobal('fetch', mockOk([MON]));

    renderTrang('/recommend?thoi_tiet=rain&cach=nuong');

    // Nhãn tiếng Việt do `chipDangBat` dịch từ mã backend.
    expect(await screen.findByText('Trời mưa')).toBeInTheDocument();
    expect(screen.getByText('Đồ nướng')).toBeInTheDocument();
  });

  it('không có món nào thì nói rõ cách gỡ, không để trang trắng', async () => {
    vi.stubGlobal('fetch', mockOk([]));

    renderTrang();

    expect(await screen.findByText(/Không có món nào khớp/)).toBeInTheDocument();
  });
  it('"Có thể bạn sẽ thích" chỉ hiện 5 món, KHÔNG đổ hết danh sách ra', async () => {
    // Lỗi thật 2026-08-26, chủ dự án báo: "đang hiển thị quá nhiều". Bản cũ đổ toàn bộ
    // phần đuôi (ở đây là 24 món) thành một lưới dài lê thê.
    const nhieuMon = Array.from({ length: 30 }, (_, i) => ({
      ...MON,
      dish_id: `mon-${i}`,
      name: `Món số ${i}`,
      rank_position: i + 1,
    }));
    vi.stubGlobal('fetch', mockOk(nhieuMon));

    renderTrang();
    // Món đầu xuất hiện hai lần: trên thẻ lớn và trong ô thông tin bên cạnh.
    await screen.findAllByText('Món số 0');

    // 6 món đầu thuộc khối "phù hợp nhất" (1 lớn + 5 nhỏ), 5 món tiếp là "có thể thích".
    expect(screen.getByText('Món số 10')).toBeInTheDocument();  // món thứ 11 = cuối khối
    expect(screen.queryByText('Món số 11')).not.toBeInTheDocument();
    expect(screen.queryByText('Món số 29')).not.toBeInTheDocument();
  });

  it('khối "có thể thích" bày HÀNG NGANG trượt, không phải lưới', async () => {
    const nhieuMon = Array.from({ length: 12 }, (_, i) => ({
      ...MON,
      dish_id: `mon-${i}`,
      name: `Món số ${i}`,
    }));
    const { container } = render_(nhieuMon);
    // Món đầu xuất hiện hai lần: trên thẻ lớn và trong ô thông tin bên cạnh.
    await screen.findAllByText('Món số 0');

    // Lưới đẩy mọi thứ phía dưới (kể cả khối "đã lưu") ra khỏi màn hình.
    expect(container.querySelector('.dishes--grid')).toBeNull();
    expect(container.querySelectorAll('.dishes--row').length).toBeGreaterThan(0);
  });
});

/** Như `renderTrang` nhưng trả `container` để soi class bày trí. */
function render_(monList: unknown[]) {
  vi.stubGlobal('fetch', mockOk(monList));
  return renderTrang();
}
