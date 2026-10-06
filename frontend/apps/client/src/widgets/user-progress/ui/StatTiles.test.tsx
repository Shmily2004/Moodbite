/**
 * `None ≠ 0` (audit 2026-10-06): đang tải / tải lỗi thì ô số liệu server KHÔNG được hiện 0.
 */
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { StatTiles } from './StatTiles';

const STATS = {
  saved_dishes: 3,
  saved_restaurants: 0,
  explorations: 7,
} as unknown as Parameters<typeof StatTiles>[0]['stats'];

function giaTri(container: HTMLElement) {
  return [...container.querySelectorAll('.stat__value')].map((n) => n.textContent);
}

describe('StatTiles', () => {
  it('dang tai -> "…" thay vi 0', () => {
    const { container } = render(<StatTiles stats={null} viewedLocal={2} loading />);
    expect(giaTri(container)).toEqual(['…', '…', '2', '…']);
  });

  it('loi -> "—" kem cau bao va nut thu lai', () => {
    const onRetry = vi.fn();
    const { container } = render(
      <StatTiles stats={null} viewedLocal={0} error="Không tải được số liệu." onRetry={onRetry} />,
    );
    expect(giaTri(container)).toEqual(['—', '—', '0', '—']);
    expect(screen.getByText(/Không tải được số liệu/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Thử lại' }));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it('co so that -> hien dung, ke ca 0 THAT', () => {
    const { container } = render(<StatTiles stats={STATS} viewedLocal={1} />);
    expect(giaTri(container)).toEqual(['3', '0', '1', '7']);
  });
});
