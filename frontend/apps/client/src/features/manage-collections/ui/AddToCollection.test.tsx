/**
 * Tạo bộ OK nhưng THÊM lỗi → bấm lại phải thêm vào bộ VỪA TẠO, không tạo bộ trùng tên
 * (audit 2026-10-06).
 */
import { describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';
import type { UseCollectionsResult } from '../model/useCollections';
import { AddToCollection } from './AddToCollection';

function giaLap(collections: UseCollectionsResult['collections']): UseCollectionsResult {
  return {
    collections,
    loading: false,
    error: null,
    busy: false,
    create: vi.fn(),
    rename: vi.fn(),
    remove: vi.fn(),
    addItem: vi.fn().mockResolvedValue(true),
    createAndAdd: vi.fn().mockResolvedValue({ added: false, createdId: 'moi' }),
    removeItem: vi.fn(),
  } as unknown as UseCollectionsResult;
}

const MUC = { itemType: 'dish', itemId: 'bun-cha', name: 'Bún chả' } as const;

describe('AddToCollection', () => {
  it('tao xong ma them loi -> lan bam sau them vao bo vua tao', async () => {
    const bo = giaLap([]);
    const { rerender } = render(<AddToCollection boSuuTap={bo} muc={MUC} />);
    fireEvent.click(screen.getByRole('button'));
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Hẹn hò' } });

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Thêm/ }));
    });
    expect(bo.createAndAdd).toHaveBeenCalledTimes(1);

    // Hook đã chèn bộ mới vào danh sách sau khi tạo thành công.
    const sau = { ...bo, collections: [{ id: 'moi', name: 'Hẹn hò', items: [], itemCount: 0 }] };
    rerender(<AddToCollection boSuuTap={sau as unknown as UseCollectionsResult} muc={MUC} />);
    expect((screen.getByRole('combobox') as HTMLSelectElement).value).toBe('moi');

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Thêm/ }));
    });
    expect(bo.createAndAdd).toHaveBeenCalledTimes(1);
    expect(bo.addItem).toHaveBeenCalledWith('moi', MUC);
  });
});
