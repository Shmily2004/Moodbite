/**
 * Bộ lọc món sau đợt đối chiếu `design/Filler.png` (2026-10-02):
 *   - công tắc giá là CÔNG TẮC thật (role="switch") cho bàn phím/trình đọc màn hình;
 *   - lời giải thích thu gọn sau nút ⓘ nhưng VẪN là mô tả của công tắc;
 *   - thứ tự nhóm theo bản thiết kế.
 */
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { LanguageProvider } from '@/shared/i18n';
import { EMPTY_FILTERS } from '../model/useDishFilterState';
import { DishFilters } from './DishFilters';

function renderLoc(overrides: Partial<typeof EMPTY_FILTERS> = {}) {
  const onSetOnlyWithPrice = vi.fn();
  const utils = render(
    <LanguageProvider>
      <DishFilters
        filters={{ ...EMPTY_FILTERS, ...overrides }}
        onToggle={vi.fn()}
        onSetSingle={vi.fn()}
        onSetMaxDistanceKm={vi.fn()}
        onSetOnlyWithPrice={onSetOnlyWithPrice}
        onReset={vi.fn()}
        activeFilterCount={0}
        locationIsDefault
        locationLoading={false}
        onRequestLocation={vi.fn()}
      />
    </LanguageProvider>,
  );
  return { ...utils, onSetOnlyWithPrice };
}

describe('DishFilters - cong tac "Chi hien quan co ghi gia"', () => {
  it('la mot switch co ten, bam duoc va bao len tren', () => {
    const { onSetOnlyWithPrice } = renderLoc();
    const congTac = screen.getByRole('switch', { name: /Chỉ hiện quán có ghi giá/ });
    expect(congTac).not.toBeChecked();
    fireEvent.click(congTac);
    expect(onSetOnlyWithPrice).toHaveBeenCalledWith(true);
  });

  it('dang bat thi switch o trang thai checked', () => {
    renderLoc({ onlyWithPrice: true });
    expect(screen.getByRole('switch', { name: /Chỉ hiện quán có ghi giá/ })).toBeChecked();
  });

  it('loi giai thich THU GON nhung van la mo ta cua cong tac, mo ra duoc bang nut i', () => {
    renderLoc();
    const congTac = screen.getByRole('switch', { name: /Chỉ hiện quán có ghi giá/ });
    // Trình đọc màn hình vẫn đọc được lời giải thích dù đang thu gọn.
    expect(congTac).toHaveAccessibleDescription(/chưa có giá/);

    const nutI = screen.getByRole('button', { name: /Vì sao bật lên/ });
    expect(nutI).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getByText(/Phần lớn quán trong dữ liệu/)).not.toBeVisible();

    fireEvent.click(nutI);
    expect(nutI).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText(/Phần lớn quán trong dữ liệu/)).toBeVisible();
  });
});

describe('DishFilters - thu tu nhom theo Filler.png', () => {
  it('mon gi -> khoang cach -> gia -> bua -> tam trang -> thoi tiet', () => {
    const { container } = renderLoc();
    const nhan = Array.from(container.querySelectorAll('.filters__row > .filters__label')).map(
      (el) => el.textContent,
    );
    expect(nhan).toEqual(['Muốn ăn gì?', 'Khoảng cách', 'Bữa nào?', 'Tâm trạng', 'Thời tiết']);
    // Công tắc giá nằm GIỮA khoảng cách và bữa ăn.
    const hang = Array.from(container.querySelectorAll('.filters > .filters__row'));
    expect(hang[2]).toHaveClass('filters__row--price');
  });
});
