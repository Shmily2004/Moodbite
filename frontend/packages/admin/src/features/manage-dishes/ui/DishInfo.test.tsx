/** Sửa mô tả món ngay trên trang quản trị: gửi đúng chữ, báo lỗi tại chỗ, gỡ bản sửa. */
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { AdminDishDetail } from '@admin/shared/api';
import { DishInfo } from './DishInfo';

function mon(overrides: Partial<AdminDishDetail> = {}): AdminDishDetail {
  return {
    dish_id: 'pho-bo',
    name: 'Phở bò',
    description: 'Mô tả gốc của phở bò.',
    is_category: false,
    is_active: true,
    meal_times: [],
    match_keywords: [],
    mo_ta_da_sua: false,
    ...overrides,
  } as AdminDishDetail;
}

describe('DishInfo — sửa mô tả', () => {
  it('không truyền hàm lưu thì KHÔNG có nút sửa (giữ nguyên chế độ chỉ đọc)', () => {
    render(<DishInfo data={mon()} />);
    expect(screen.queryByRole('button', { name: 'Sửa mô tả' })).toBeNull();
    expect(screen.getByText('Mô tả gốc của phở bò.')).toBeInTheDocument();
  });

  it('sửa rồi Lưu -> gửi đúng chữ đã cắt khoảng trắng và thoát chế độ sửa', async () => {
    const luu = vi.fn().mockResolvedValue(null);
    render(<DishInfo data={mon()} onLuuMoTa={luu} />);

    fireEvent.click(screen.getByRole('button', { name: 'Sửa mô tả' }));
    const o = screen.getByLabelText('Mô tả món');
    expect(o).toHaveValue('Mô tả gốc của phở bò.');
    fireEvent.change(o, { target: { value: 'Phở bò nước dùng trong, thịt tái.' } });
    fireEvent.click(screen.getByRole('button', { name: 'Lưu' }));

    await waitFor(() => expect(luu).toHaveBeenCalledWith('Phở bò nước dùng trong, thịt tái.'));
    await waitFor(() => expect(screen.queryByLabelText('Mô tả món')).toBeNull());
  });

  it('lưu lỗi -> giữ nguyên ô sửa và hiện lỗi ngay tại đó', async () => {
    const luu = vi.fn().mockResolvedValue('Mô tả quá dài.');
    render(<DishInfo data={mon()} onLuuMoTa={luu} />);

    fireEvent.click(screen.getByRole('button', { name: 'Sửa mô tả' }));
    fireEvent.click(screen.getByRole('button', { name: 'Lưu' }));

    expect(await screen.findByText('Mô tả quá dài.')).toBeInTheDocument();
    expect(screen.getByLabelText('Mô tả món')).toBeInTheDocument();
  });

  it('đang là bản sửa tay -> hiện nhãn và nút Gỡ bản sửa gửi null', async () => {
    const luu = vi.fn().mockResolvedValue(null);
    render(<DishInfo data={mon({ mo_ta_da_sua: true })} onLuuMoTa={luu} />);

    expect(screen.getByText(/bản do quản trị viên sửa tay/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Gỡ bản sửa' }));
    await waitFor(() => expect(luu).toHaveBeenCalledWith(null));
  });

  it('chưa sửa lần nào thì KHÔNG có nút Gỡ bản sửa', () => {
    render(<DishInfo data={mon()} onLuuMoTa={vi.fn()} />);
    expect(screen.queryByRole('button', { name: 'Gỡ bản sửa' })).toBeNull();
  });
});
