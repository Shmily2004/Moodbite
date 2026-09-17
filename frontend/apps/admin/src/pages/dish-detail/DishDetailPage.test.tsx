/**
 * Test trang CHI TIẾT MÓN (`/mon-an/:dishId`).
 *
 * Canh: rating `null` hiện "chưa có đánh giá" (không phải 0) · lịch sử rỗng nói rõ ·
 * không bày nút thao tác mà backend chưa hỗ trợ.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

const { getDish, dishRestaurants, activity } = vi.hoisted(() => ({
  getDish: vi.fn(),
  dishRestaurants: vi.fn(),
  activity: vi.fn(),
}));

vi.mock('@/shared/api', async () => {
  const that = await vi.importActual<typeof import('@/shared/api')>('@/shared/api');
  return { ...that, adminApi: { getDish, dishRestaurants, activity } };
});

import { DishDetailPage } from './ui/DishDetailPage';

afterEach(() => {
  vi.clearAllMocks();
  vi.restoreAllMocks();
});

describe('Trang chi tiet mon', () => {
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    getDish.mockResolvedValue({
      dish_id: 'bun-cha',
      name: 'Bún chả',
      cuisine: 'Việt Nam',
      image_url: null,
      description: 'Bún ăn với chả nướng',
      is_category: false,
      is_active: true,
      source: 'wikipedia_vi',
      last_updated: null,
      restaurant_count: 426,
    });
    dishRestaurants.mockResolvedValue({
      dish_id: 'bun-cha',
      total: 426,
      results: [
        {
          restaurant_id: 'r1',
          name: 'Bún Chả Hương Liên',
          address: '24 Lê Văn Hưu',
          district: 'Phường Hai Bà Trưng',
          rating: null,
          reviews_count: null,
          source: 'openstreetmap',
          matched_by: 'dish_name',
        },
      ],
    });
    activity.mockResolvedValue({ entries: [], total: 0, available: true });
  });

  function moChiTiet(path = '/mon-an/bun-cha') {
    return render(
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/mon-an/:dishId" element={<DishDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );
  }

  it('co link quay lai, tab so quan, rating null hien "chua co danh gia"', async () => {
    moChiTiet();

    expect(await screen.findByRole('heading', { name: 'Bún chả' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Quay lại danh sách món ăn/ })).toHaveAttribute(
      'href',
      '/mon-an',
    );
    expect(screen.getByRole('tab', { name: /Danh sách quán \(426\)/ })).toBeInTheDocument();
    expect(await screen.findByText('chưa có đánh giá')).toBeInTheDocument();
    expect(screen.getByText('Nguồn: OpenStreetMap')).toBeInTheDocument();
    expect(activity).toHaveBeenCalledWith(
      expect.objectContaining({ targetType: 'dish', targetId: 'bun-cha' }),
    );
  });

  it('lich su rong thi noi ro, KHONG de trang trong', async () => {
    moChiTiet('/mon-an/bun-cha?tab=lich-su');

    expect(
      await screen.findByText(/Chưa có thay đổi nào được ghi cho món này/),
    ).toBeInTheDocument();
  });

  it('KHONG bay nut thao tac ma backend chua ho tro', async () => {
    moChiTiet();
    await screen.findByRole('heading', { name: 'Bún chả' });

    expect(screen.queryByRole('button', { name: /Chỉnh sửa|Ngừng hoạt động/ })).toBeNull();
  });
});
