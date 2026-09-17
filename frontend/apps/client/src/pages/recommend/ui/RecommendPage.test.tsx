/**
 * Trang KẾT QUẢ GỢI Ý MÓN.
 *
 * Thứ đáng khoá nhất ở đây là BỘ LỌC ĐI QUA URL — vì nó là lý do trang này tách ra được
 * khỏi trang chủ. Sai một tên tham số là đường dẫn đã chia sẻ không còn lọc đúng nữa,
 * mà không có gì báo lỗi.
 */
import { describe, expect, it, vi, afterEach } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { UserSessionProvider } from '@/entities/user';
import { LanguageProvider } from '@/shared/i18n';
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

/** Trang món giả: in ra đường dẫn + query nhận được. */
function TrangMonGia() {
  const { pathname, search } = useLocation();
  return <p data-testid="trang-mon">{pathname + search}</p>;
}

function renderTrang(duongDan = '/recommend') {
  // `SiteHeader` bên trong trang đọc phiên đăng nhập -> phải bọc provider, đúng như
  // `RootLayout` làm lúc chạy thật.
  return render(
    <MemoryRouter initialEntries={[duongDan]}>
      <LanguageProvider>
        <UserSessionProvider>
          <Routes>
            <Route path="/recommend" element={<RecommendPage />} />
            <Route path="/dishes/:dishId" element={<TrangMonGia />} />
          </Routes>
        </UserSessionProvider>
      </LanguageProvider>
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

  it('tiêu đề đếm số món: "N món ăn phù hợp" (Filler.png)', async () => {
    vi.stubGlobal('fetch', mockOk([MON, { ...MON, dish_id: 'pho-bo', name: 'Phở bò' }]));

    renderTrang();

    expect(
      await screen.findByRole('heading', { level: 1, name: '2 món ăn phù hợp' }),
    ).toBeInTheDocument();
  });

  it('có CỘT LỌC cố định (FilterDrawer inline) và lưới món', async () => {
    vi.stubGlobal('fetch', mockOk([MON]));

    const { container } = renderTrang();
    await screen.findAllByText('Bún chả');

    // Cột trái là `aside` inline — ẩn/hiện theo bề rộng do CSS lo (≥1024px).
    expect(container.querySelector('aside.drawer--inline')).not.toBeNull();
    // Kết quả là LƯỚI (3/2/1 cột do CSS), không còn hàng ngang trượt.
    expect(container.querySelector('.recommend__luoi .dishes--grid')).not.toBeNull();
    // Cột lọc dùng thanh trượt bán kính.
    expect(screen.getByRole('slider')).toBeInTheDocument();
  });

  it('"Đang lọc theo:" liệt kê chip (kể cả bán kính) và gỡ được từng cái', async () => {
    vi.stubGlobal('fetch', mockOk([MON]));

    renderTrang('/recommend?thoi_tiet=rain&cach=nuong&km=3');

    const dangLoc = await screen.findByRole('group', { name: 'Đang lọc theo:' });
    // Nhãn tiếng Việt do `chipDangBat` dịch từ mã backend.
    expect(within(dangLoc).getByText('Trời mưa')).toBeInTheDocument();
    expect(within(dangLoc).getByText('Đồ nướng')).toBeInTheDocument();
    expect(within(dangLoc).getByText('Trong vòng 3 km')).toBeInTheDocument();

    fireEvent.click(within(dangLoc).getByRole('button', { name: /Trời mưa/ }));
    await waitFor(() =>
      expect(within(dangLoc).queryByText('Trời mưa')).not.toBeInTheDocument(),
    );
  });

  it('"Xoá tất cả" gỡ hết chip đang lọc', async () => {
    vi.stubGlobal('fetch', mockOk([MON]));

    renderTrang('/recommend?thoi_tiet=rain&bua=toi');

    const dangLoc = await screen.findByRole('group', { name: 'Đang lọc theo:' });
    fireEvent.click(within(dangLoc).getByRole('button', { name: 'Xoá tất cả' }));

    await waitFor(() =>
      expect(screen.queryByRole('group', { name: 'Đang lọc theo:' })).not.toBeInTheDocument(),
    );
  });

  it('ô sắp xếp CHỈ có kiểu làm được thật, và sắp lại theo tên', async () => {
    // API không có tham số sort -> không được vẽ "Gần nhất" / "Đánh giá cao".
    vi.stubGlobal(
      'fetch',
      mockOk([
        { ...MON, dish_id: 'pho', name: 'Phở bò', restaurant_count: 5 },
        { ...MON, dish_id: 'bun', name: 'Bún chả', restaurant_count: 50 },
      ]),
    );
    const { container } = renderTrang();
    await screen.findAllByText('Phở bò');

    const oSapXep = screen.getByRole('combobox', { name: /Sắp xếp/ });
    expect(within(oSapXep).getAllByRole('option').map((o) => o.textContent)).toEqual([
      'Phù hợp nhất',
      'Tên A–Z',
      'Nhiều quán gần bạn nhất',
    ]);

    const tenTrongLuoi = () =>
      [...container.querySelectorAll('.recommend__luoi .dishcard__name')].map(
        (n) => n.textContent,
      );
    // Mặc định giữ NGUYÊN thứ tự backend.
    expect(tenTrongLuoi()).toEqual(['Phở bò', 'Bún chả']);

    fireEvent.change(oSapXep, { target: { value: 'ten' } });
    expect(tenTrongLuoi()).toEqual(['Bún chả', 'Phở bò']);
  });

  it('lưới chỉ hiện 9 món đầu, có nút "Xem thêm N món"', async () => {
    // Chủ dự án từng chê trang này "hiển thị quá nhiều" (2026-08-26).
    const nhieuMon = Array.from({ length: 30 }, (_, i) => ({
      ...MON,
      dish_id: `mon-${i}`,
      name: `Món số ${i}`,
      rank_position: i + 1,
    }));
    vi.stubGlobal('fetch', mockOk(nhieuMon));

    renderTrang();
    await screen.findByText('Món số 0');

    expect(screen.getByText('Món số 8')).toBeInTheDocument();
    expect(screen.queryByText('Món số 9')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Xem thêm 21 món/ }));
    expect(screen.getByText('Món số 29')).toBeInTheDocument();
  });

  it('mở một món thì MANG THEO bộ lọc sang trang món (để "Chỉnh sửa" mở lại đúng)', async () => {
    vi.stubGlobal('fetch', mockOk([MON]));

    const { container } = renderTrang('/recommend?thoi_tiet=rain&km=3');
    await screen.findByText('Bún chả');
    fireEvent.click(container.querySelector('.recommend__luoi article.dishcard') as HTMLElement);

    const dich = await screen.findByTestId('trang-mon');
    expect(dich.textContent).toMatch(/^\/dishes\/bun-cha\?/);
    expect(dich.textContent).toContain('thoi_tiet=rain');
    expect(dich.textContent).toContain('km=3');
  });

  it('KHÁCH thấy dải "Muốn MoodBite hiểu bạn hơn?"', async () => {
    vi.stubGlobal('fetch', mockOk([MON]));

    renderTrang();

    expect(await screen.findByText(/Muốn MoodBite hiểu bạn hơn/)).toBeInTheDocument();
  });

  it('không có món nào thì nói rõ cách gỡ, không để trang trắng', async () => {
    vi.stubGlobal('fetch', mockOk([]));

    renderTrang();

    expect(await screen.findByText(/Không có món nào khớp/)).toBeInTheDocument();
  });
});
