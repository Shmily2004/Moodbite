/**
 * Ngăn kéo bộ lọc — cụ thể là NÚT "XEM KẾT QUẢ" DẪN ĐI ĐÂU.
 *
 * Khoá lại lỗi luồng chủ dự án phát hiện 2026-08-26: ở trang chủ, chọn xong bộ lọc mà
 * chỉ đóng ngăn kéo thì người dùng vẫn đứng nguyên trang chủ — cụt luồng. Nút đó phải
 * dẫn sang `/recommend`.
 */
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { LanguageProvider } from '@/shared/i18n';
import { FilterDrawer } from '../index';

function moNganKeo(props: Partial<Parameters<typeof FilterDrawer>[0]> = {}) {
  const onClose = vi.fn();
  const onApply = vi.fn();
  render(
    <LanguageProvider>
      <FilterDrawer
        open
        onClose={onClose}
        activeCount={0}
        onReset={() => {}}
        {...props}
      >
        <p>nội dung bộ lọc</p>
      </FilterDrawer>
    </LanguageProvider>,
  );
  return { onClose, onApply };
}

describe('FilterDrawer — nút "Xem kết quả"', () => {
  it('có onApply thì GỌI onApply, không chỉ đóng', () => {
    const onClose = vi.fn();
    const onApply = vi.fn();
    render(
      <LanguageProvider>
        <FilterDrawer open onClose={onClose} activeCount={0} onReset={() => {}} onApply={onApply}>
          <p>nội dung bộ lọc</p>
        </FilterDrawer>
      </LanguageProvider>,
    );

    // Nút cuối cùng trong ngăn kéo là "Xem kết quả" ở chân.
    const nut = screen.getAllByRole('button');
    fireEvent.click(nut[nut.length - 1]);

    expect(onApply).toHaveBeenCalledTimes(1);
    expect(onClose).not.toHaveBeenCalled();
  });

  it('KHÔNG truyền onApply thì lui về đóng ngăn kéo', () => {
    // Ở chính `/recommend` thì đã đúng trang rồi, đóng là đủ.
    const { onClose } = moNganKeo();

    const nut = screen.getAllByRole('button');
    fireEvent.click(nut[nut.length - 1]);

    expect(onClose).toHaveBeenCalled();
  });

  it('đóng lại khi bấm Esc', () => {
    const { onClose } = moNganKeo();

    fireEvent.keyDown(document, { key: 'Escape' });

    expect(onClose).toHaveBeenCalled();
  });
});
