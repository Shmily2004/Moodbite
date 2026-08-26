/**
 * Bong bóng trợ lý.
 *
 * Khoá lại đúng những chỗ đã làm sai một lần (2026-08-26): mascot phải đứng RIÊNG chứ
 * không nằm trong nút, và nút phải là nút thật bấm được chứ không phải khối trang trí.
 */
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { AssistantBubble } from '../index';

describe('AssistantBubble', () => {
  it('bấm vào thì báo lên trên để trang mở bộ lọc', () => {
    const moBoLoc = vi.fn();
    render(<AssistantBubble onOpen={moBoLoc} />);

    fireEvent.click(screen.getByRole('button'));

    expect(moBoLoc).toHaveBeenCalledTimes(1);
  });

  it('mascot nằm NGOÀI nút, không phải icon bên trong nút', () => {
    // Bản đầu nhét mascot vào trong <button>, sai với thiết kế: mascot là nhân vật
    // đứng cạnh. Nếu ai đó gộp lại, test này đỏ.
    const { container } = render(<AssistantBubble onOpen={() => {}} />);

    const nut = screen.getByRole('button');
    const mascot = container.querySelector('.bubble__mascot');

    expect(mascot).not.toBeNull();
    expect(nut.contains(mascot)).toBe(false);
  });

  it('hiện số bộ lọc đang bật, và ẩn khi chưa lọc gì', () => {
    const { container, rerender } = render(<AssistantBubble onOpen={() => {}} activeCount={3} />);
    expect(container.querySelector('.bubble__dem')?.textContent).toBe('3');

    rerender(<AssistantBubble onOpen={() => {}} activeCount={0} />);
    // Số 0 mà vẫn hiện thì người dùng tưởng đang có bộ lọc nào đó bật.
    expect(container.querySelector('.bubble__dem')).toBeNull();
  });

  it('lời thoại bị ẩn với trình đọc màn hình để khỏi đọc lặp với nút', () => {
    const { container } = render(<AssistantBubble onOpen={() => {}} />);

    expect(container.querySelector('.bubble__thoai')).toHaveAttribute('aria-hidden', 'true');
  });
});
