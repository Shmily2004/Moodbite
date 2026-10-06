/**
 * Chọn điểm KHÔNG cần chuột (audit 2026-10-06): bị chặn định vị thì người dùng bàn phím
 * vẫn phải đặt được ghim — nút "Đặt ghim ở tâm bản đồ".
 */
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { HANOI_CENTER } from '@/shared/config';
import { PointPickerMap } from './PointPickerMap';

describe('PointPickerMap', () => {
  it('nut "Dat ghim o tam ban do" chon dung tam khung dang nhin', async () => {
    const onPick = vi.fn();
    render(<PointPickerMap point={null} onPick={onPick} />);

    const nut = screen.getByRole('button', { name: 'Đặt ghim ở tâm bản đồ' });
    await waitFor(() => expect(nut).not.toBeDisabled());
    fireEvent.click(nut);

    expect(onPick).toHaveBeenCalledOnce();
    const diem = onPick.mock.calls[0][0] as { lat: number; lng: number };
    expect(diem.lat).toBeCloseTo(HANOI_CENTER.lat, 4);
    expect(diem.lng).toBeCloseTo(HANOI_CENTER.lng, 4);
  });
});
