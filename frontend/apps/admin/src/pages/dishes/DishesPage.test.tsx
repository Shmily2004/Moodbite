/**
 * Test màn "Quản lý món ăn".
 *
 * Canh: số trên nút lọc lấy từ backend · "Có quán" `null` hiện "—" chứ không phải 0 ·
 * thiếu ngày cập nhật hiện "—" · đổi trang gọi lại API với `page`.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

const { listDishes } = vi.hoisted(() => ({
  listDishes: vi.fn(),
}));

vi.mock('@/shared/api', async () => {
  const that = await vi.importActual<typeof import('@/shared/api')>('@/shared/api');
  return { ...that, adminApi: { listDishes } };
});

import { DishesPage } from './ui/DishesPage';

function mocDanhSach(ghiDe: Record<string, unknown> = {}) {
  return {
    results: [
      {
        dish_id: 'bun-cha',
        name: 'Bún chả',
        cuisine: 'Việt Nam',
        image_url: null,
        has_description: true,
        description: 'Bún ăn với chả nướng',
        is_category: false,
        is_active: true,
        source: 'wikipedia_vi',
        last_updated: null,
        restaurant_count: 426,
      },
      {
        dish_id: 'kem-bo',
        name: 'Kem bơ',
        cuisine: null,
        image_url: null,
        has_description: false,
        description: null,
        is_category: false,
        is_active: false,
        source: 'manual',
        last_updated: null,
        restaurant_count: null,
      },
    ],
    returned: 2,
    total: 45,
    page: 1,
    page_size: 20,
    counts: {
      all: 855,
      with_restaurants: 298,
      without_restaurants: 557,
      missing_image: 102,
      missing_description: 60,
    },
    dishes_total: 855,
    dishes_with_restaurants: 298,
    ...ghiDe,
  };
}

beforeEach(() => {
  listDishes.mockResolvedValue(mocDanhSach());
  vi.spyOn(console, 'error').mockImplementation(() => {});
  vi.spyOn(console, 'warn').mockImplementation(() => {});
});

afterEach(() => {
  vi.clearAllMocks();
  vi.restoreAllMocks();
});

describe('Man "Quan ly mon an"', () => {
  function moTrang() {
    return render(
      <MemoryRouter initialEntries={['/mon-an']}>
        <Routes>
          <Route path="/mon-an" element={<DishesPage />} />
        </Routes>
      </MemoryRouter>,
    );
  }

  it('the so + so tren nut loc lay tu backend', async () => {
    moTrang();

    const the = within(await screen.findByRole('list', { name: /Tổng hợp món/ }));
    expect(the.getByText(/34,9%/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Chưa có quán\s*557/ })).toBeInTheDocument();
  });

  it('co quan null hien "—", KHONG hien 0; thieu ngay cap nhat hien "—"', async () => {
    moTrang();

    const dongKem = (await screen.findByRole('link', { name: 'Kem bơ' })).closest('tr');
    expect(dongKem).not.toBeNull();
    const o = within(dongKem as HTMLElement).getAllByRole('cell');
    // Cột 3 = "Có quán"
    expect(o[2]).toHaveTextContent('—');
    expect(o[2]).not.toHaveTextContent('0');
    expect(o[6]).toHaveTextContent('—');
  });

  it('link sang trang chi tiet mon la route that', async () => {
    moTrang();

    expect(await screen.findByRole('link', { name: 'Bún chả' })).toHaveAttribute(
      'href',
      '/mon-an/bun-cha',
    );
  });

  it('doi trang thi goi lai API voi page moi', async () => {
    moTrang();
    await screen.findByText(/Hiển thị 1–20 của 45 món/);

    fireEvent.click(screen.getByRole('button', { name: '2' }));

    await waitFor(() =>
      expect(listDishes).toHaveBeenLastCalledWith(expect.objectContaining({ page: 2 })),
    );
  });
});
