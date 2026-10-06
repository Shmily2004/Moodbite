/** Ô tìm quán: gõ liền nhiều phím chỉ gửi MỘT lần, sau khi ngừng gõ (audit 2026-10-06). */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { OTimQuan, TRE_MS } from './OTimQuan';

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

describe('OTimQuan', () => {
  it('go "pho" tung phim -> chi gui 1 lan, sau TRE_MS', () => {
    const onQuery = vi.fn();
    render(<OTimQuan q="" onQuery={onQuery} />);
    const o = screen.getByRole('textbox', { name: 'Tìm quán' });

    for (const v of ['p', 'ph', 'pho']) fireEvent.change(o, { target: { value: v } });
    expect(onQuery).not.toHaveBeenCalled();
    expect(o).toHaveValue('pho');

    act(() => vi.advanceTimersByTime(TRE_MS));
    expect(onQuery).toHaveBeenCalledTimes(1);
    expect(onQuery).toHaveBeenCalledWith('pho');
  });

  it('URL doi tu ngoai (Xoa bo loc) -> o nhap dong bo theo', () => {
    const onQuery = vi.fn();
    const { rerender } = render(<OTimQuan q="pho" onQuery={onQuery} />);
    rerender(<OTimQuan q="" onQuery={onQuery} />);
    expect(screen.getByRole('textbox', { name: 'Tìm quán' })).toHaveValue('');
    act(() => vi.advanceTimersByTime(TRE_MS));
    expect(onQuery).not.toHaveBeenCalled();
  });
});
