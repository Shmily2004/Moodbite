/**
 * Dải món trang chủ: nút cuộn trái/phải (2026-10-02) và nhãn thuộc tính ở lưới `/recommend`.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import type { DishItem } from '@/shared/api';
import { LanguageProvider } from '@/shared/i18n';
import { DishList } from './DishList';

function mon(i: number, extra: Partial<DishItem> = {}): DishItem {
  return {
    dish_id: `m${i}`,
    name: `Món ${i}`,
    cuisine: 'Việt Nam',
    spice_level: 0,
    temperature: 'hot',
    cooking_method: 'nuoc',
    meal_times: [],
    has_description: false,
    description: null,
    image_url: null,
    restaurant_count: 12877,
    nearest_restaurant_km: null,
    rank_position: i,
    score: 0.5,
    reasons: [],
    source: null,
    source_url: null,
    data_confidence: null,
    is_category: false,
    ...extra,
  } as DishItem;
}

/** jsdom không tính bố cục: tự đặt kích thước để giả lập dải bị TRÀN ngang. */
function giaLapKichThuoc(scrollWidth: number, clientWidth: number) {
  vi.spyOn(HTMLElement.prototype, 'scrollWidth', 'get').mockReturnValue(scrollWidth);
  vi.spyOn(HTMLElement.prototype, 'clientWidth', 'get').mockReturnValue(clientWidth);
}

function renderDs(layout: 'row' | 'grid' = 'row') {
  return render(
    <LanguageProvider>
      <DishList dishes={[mon(1), mon(2), mon(3)]} onOpen={vi.fn()} layout={layout} />
    </LanguageProvider>,
  );
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe('DishList - nut cuon dai ngang', () => {
  it('dai VUA KHIT man hinh thi khong ve nut nao (khong bay nut chet)', () => {
    giaLapKichThuoc(600, 600);
    renderDs();
    expect(screen.queryByRole('button', { name: /Cuộn sang/ })).not.toBeInTheDocument();
  });

  it('dai TRAN ben phai thi co nut "tiep theo" co ten doc duoc, bam thi cuon', () => {
    giaLapKichThuoc(1500, 600);
    const cuon = vi.fn();
    HTMLElement.prototype.scrollBy = cuon as unknown as typeof HTMLElement.prototype.scrollBy;
    renderDs();

    // Đang ở đầu dải: chỉ có nút sang phải.
    expect(screen.queryByRole('button', { name: /món trước/ })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /món tiếp theo/ }));
    expect(cuon).toHaveBeenCalledWith(expect.objectContaining({ left: 480 }));
  });

  it('luoi (grid) khong co nut cuon', () => {
    giaLapKichThuoc(1500, 600);
    renderDs('grid');
    expect(screen.queryByRole('button', { name: /Cuộn sang/ })).not.toBeInTheDocument();
  });
});

describe('DishList - nhan thuoc tinh mon', () => {
  it('luoi /recommend hien nhan (Món nước · Việt Nam · Nóng) va so quan co dau cham', () => {
    renderDs('grid');
    expect(screen.getAllByText('Món nước')).toHaveLength(3);
    expect(screen.getAllByText('Việt Nam')).toHaveLength(3);
    expect(screen.getAllByText('12.877 quán gần bạn')).toHaveLength(3);
  });

  it('dai ngang trang chu giu the gon, KHONG hien nhan', () => {
    renderDs('row');
    expect(screen.queryByText('Món nước')).not.toBeInTheDocument();
  });
});
