/**
 * Test ảnh thu nhỏ có đường lui.
 *
 * Canh: link chết KHÔNG BAO GIỜ để lại biểu tượng "ảnh vỡ" của trình duyệt · không có link
 * thì ra ô giữ chỗ trống, không phải ảnh mẫu · đổi sang link mới thì thử lại.
 */
import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { AnhThuNho } from './AnhThuNho';

describe('AnhThuNho', () => {
  it('khong co link thi hien o giu cho, KHONG co the img', () => {
    const { container } = render(
      <AnhThuNho src={null} className="o-anh" classNameTrong="o-anh--trong" />,
    );
    expect(container.querySelector('img')).toBeNull();
    expect(container.querySelector('.o-anh.o-anh--trong')).not.toBeNull();
  });

  it('link chet (onError) thi doi sang o giu cho, giu chu ben trong', () => {
    const { container } = render(
      <AnhThuNho
        src="https://vi.wikipedia.org/anh-da-chet.jpg"
        className="chi-tiet-mon__anh"
        classNameTrong="chi-tiet-mon__anh--trong"
        alt="Phở bò"
      >
        Chưa có ảnh
      </AnhThuNho>,
    );
    fireEvent.error(screen.getByRole('img', { name: 'Phở bò' }));

    expect(container.querySelector('img')).toBeNull();
    expect(screen.getByText('Chưa có ảnh')).toHaveClass('chi-tiet-mon__anh--trong');
  });

  it('doi sang link moi thi thu tai lai, khong ke thua trang thai hong', () => {
    const { container, rerender } = render(
      <AnhThuNho src="https://a.example/1.jpg" className="o-anh" classNameTrong="o-anh--trong" />,
    );
    fireEvent.error(container.querySelector('img') as HTMLImageElement);
    expect(container.querySelector('img')).toBeNull();

    rerender(
      <AnhThuNho src="https://a.example/2.jpg" className="o-anh" classNameTrong="o-anh--trong" />,
    );
    expect(container.querySelector('img')).toHaveAttribute('src', 'https://a.example/2.jpg');
  });
});
