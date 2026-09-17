/**
 * Test màn "Quản lý quán ăn": thẻ số, bộ lọc lên API, chọn nhiều + ẩn hàng loạt.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const { listRestaurants, restaurantStats, bulkSetVisibility } = vi.hoisted(() => ({
  listRestaurants: vi.fn(),
  restaurantStats: vi.fn(),
  bulkSetVisibility: vi.fn(),
}));

vi.mock('@/shared/api', async () => {
  const that = await vi.importActual<typeof import('@/shared/api')>('@/shared/api');
  return { ...that, adminApi: { listRestaurants, restaurantStats, bulkSetVisibility } };
});

import { AdminSessionProvider } from '@/features/admin-login';
import { RestaurantsPage } from './ui/RestaurantsPage';

const QUAN = [
  {
    restaurant_id: 'pho-1',
    name: 'Phở Thìn',
    address: '13 Lò Đúc',
    district: 'Phường Hai Bà Trưng',
    category: 'Nhà hàng',
    rating: null,
    reviews_count: null,
    is_active: true,
    source: 'openstreetmap',
    source_updated_at: null,
  },
  {
    restaurant_id: 'bun-2',
    name: 'Bún Chả Hương Liên',
    address: '24 Lê Văn Hưu',
    district: 'Phường Hai Bà Trưng',
    category: 'Nhà hàng',
    rating: 4.6,
    reviews_count: 1200,
    is_active: true,
    source: 'google_maps_apify',
    source_updated_at: '2026-05-20',
  },
];

function moTrang(path = '/quan-an') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AdminSessionProvider>
        <RestaurantsPage />
      </AdminSessionProvider>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  listRestaurants.mockResolvedValue({
    total: 2,
    total_matched: 52871,
    page: 1,
    page_size: 20,
    results: QUAN,
  });
  restaurantStats.mockResolvedValue({
    total: 52871,
    visible: 52800,
    hidden: 71,
    manual: 0,
    districts: [{ value: 'Phường Hoàn Kiếm', count: 3957 }],
    sources: [{ value: 'overture', count: 48406 }],
  });
  bulkSetVisibility.mockResolvedValue({
    updated: QUAN.map((q) => ({ ...q, is_active: false })),
    not_found: [],
  });
  vi.spyOn(console, 'error').mockImplementation(() => {});
  vi.spyOn(console, 'warn').mockImplementation(() => {});
});

afterEach(() => {
  vi.clearAllMocks();
  vi.restoreAllMocks();
});

describe('Man "Quan ly quan an"', () => {
  it('the so + tong khop la total_matched, rating null hien "chua co"', async () => {
    moTrang();

    const the = within(await screen.findByRole('list', { name: /Tổng hợp quán/ }));
    expect(the.getByText('52.871')).toBeInTheDocument();
    expect(await screen.findByText(/Hiển thị 1–20 của 52.871 quán/)).toBeInTheDocument();
    const dongPho = screen.getByText('Phở Thìn').closest('tr') as HTMLElement;
    expect(within(dongPho).getByText('chưa có')).toBeInTheDocument();
  });

  it('chon khu vuc thi gui bo loc len server va ve trang 1', async () => {
    moTrang('/quan-an?trang=3');
    await screen.findByText('Phở Thìn');

    fireEvent.change(screen.getByRole('combobox', { name: /Khu vực/ }), {
      target: { value: 'Phường Hoàn Kiếm' },
    });

    await waitFor(() =>
      expect(listRestaurants).toHaveBeenLastCalledWith(
        expect.objectContaining({ district: 'Phường Hoàn Kiếm', page: 1 }),
        expect.anything(),
      ),
    );
  });

  it('chon nhieu roi an hang loat goi DUNG danh sach ma', async () => {
    moTrang();
    await screen.findByText('Phở Thìn');

    const nutAn = screen.getByRole('button', { name: 'Ẩn quán' });
    expect(nutAn).toBeDisabled();

    fireEvent.click(screen.getByRole('checkbox', { name: 'Chọn Phở Thìn' }));
    fireEvent.click(screen.getByRole('checkbox', { name: 'Chọn Bún Chả Hương Liên' }));
    expect(screen.getByText('Đã chọn 2 quán')).toBeInTheDocument();

    fireEvent.click(nutAn);

    await waitFor(() =>
      expect(bulkSetVisibility).toHaveBeenCalledWith(['pho-1', 'bun-2'], false),
    );
    expect(await screen.findByText(/Đã ẩn 2 quán/)).toBeInTheDocument();
  });
});
