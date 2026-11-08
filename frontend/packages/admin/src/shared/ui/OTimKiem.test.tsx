/** Ô tìm kiếm dùng chung: gõ liền nhiều phím chỉ gửi MỘT lần, và không phá bộ gõ tiếng Việt. */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { OTimKiem, TRE_MS } from './OTimKiem';

const NHAN = 'Tìm món';
const rend = (q: string, onQuery: (v: string) => void) =>
  render(<OTimKiem q={q} onQuery={onQuery} placeholder="…" label={NHAN} />);

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

describe('OTimKiem', () => {
  it('gõ "pho" từng phím -> chỉ gửi 1 lần, sau TRE_MS', () => {
    const onQuery = vi.fn();
    rend('', onQuery);
    const o = screen.getByRole('searchbox', { name: NHAN });

    for (const v of ['p', 'ph', 'pho']) fireEvent.change(o, { target: { value: v } });
    expect(onQuery).not.toHaveBeenCalled();
    expect(o).toHaveValue('pho');

    act(() => vi.advanceTimersByTime(TRE_MS));
    expect(onQuery).toHaveBeenCalledTimes(1);
    expect(onQuery).toHaveBeenCalledWith('pho');
  });

  it('URL đổi từ ngoài (Xoá bộ lọc) -> ô nhập đồng bộ theo', () => {
    const onQuery = vi.fn();
    const { rerender } = render(
      <OTimKiem q="pho" onQuery={onQuery} placeholder="…" label={NHAN} />,
    );
    rerender(<OTimKiem q="" onQuery={onQuery} placeholder="…" label={NHAN} />);
    expect(screen.getByRole('searchbox', { name: NHAN })).toHaveValue('');
    act(() => vi.advanceTimersByTime(TRE_MS));
    expect(onQuery).not.toHaveBeenCalled();
  });

  it('đang soạn dấu (composition) -> KHÔNG gửi, dù đã qua TRE_MS', () => {
    const onQuery = vi.fn();
    rend('', onQuery);
    const o = screen.getByRole('searchbox', { name: NHAN });

    fireEvent.compositionStart(o);
    fireEvent.change(o, { target: { value: 'tr' } });
    fireEvent.change(o, { target: { value: 'trê' } });
    act(() => vi.advanceTimersByTime(TRE_MS * 3));
    expect(onQuery).not.toHaveBeenCalled();
    expect(o).toHaveValue('trê');
  });

  it('hết composition -> gửi đúng chữ đã chốt, một lần', () => {
    const onQuery = vi.fn();
    rend('', onQuery);
    const o = screen.getByRole('searchbox', { name: NHAN });

    fireEvent.compositionStart(o);
    fireEvent.change(o, { target: { value: 'chè' } });
    fireEvent.compositionEnd(o);
    expect(onQuery).not.toHaveBeenCalled();

    act(() => vi.advanceTimersByTime(TRE_MS));
    expect(onQuery).toHaveBeenCalledTimes(1);
    expect(onQuery).toHaveBeenCalledWith('chè');
  });
});
