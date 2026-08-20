/**
 * Test nút BÁO QUÁN ĐÃ ĐÓNG CỬA.
 *
 * Backend đã đếm theo PHIÊN từ 2026-08-19; phần thiếu duy nhất là cái nút. Test ở đây
 * khoá ba điều dễ làm sai nhất:
 *   1. phải hỏi lại trước khi gửi (bấm nhầm góp phần làm quán biến mất với MỌI người)
 *   2. gửi đúng `action_type: 'report_closed'` kèm `session_id` - đếm theo phiên dựa vào nó
 *   3. gửi hỏng thì phải NÓI RA, khác hẳn mọi tương tác ghi ngầm khác
 */
import { describe, expect, it, vi, beforeEach } from 'vitest';
// `fireEvent` chứ không phải `user-event`: nút này chỉ cần click thuần, và thêm một gói
// phụ thuộc mới chỉ để gõ ngắn hơn là cái giá không đáng trả cho CI.
import { fireEvent, render, screen } from '@testing-library/react';

const logInteraction = vi.fn();

vi.mock('@/shared/api', () => ({
  api: { logInteraction: (...args: unknown[]) => logInteraction(...args) },
}));
vi.mock('@/shared/lib', () => ({ getSessionId: () => 'phien-test' }));

import { ReportClosureButton } from './ReportClosureButton';

function renderNut() {
  return render(
    <ReportClosureButton restaurantId="ChIJtest" restaurantName="Bún Ốc Hương Xưa" />,
  );
}

beforeEach(() => {
  logInteraction.mockReset();
  logInteraction.mockResolvedValue({ interaction_event_id: 'e1', is_positive_signal: false });
});

describe('ReportClosureButton', () => {
  it('bấm một lần CHƯA gửi gì - phải hỏi lại trước', async () => {
    renderNut();
    fireEvent.click(screen.getByRole('button', { name: /đã đóng cửa/i }));

    expect(logInteraction).not.toHaveBeenCalled();
    expect(screen.getByText(/xác nhận/i)).toBeInTheDocument();
    // Tên quán phải xuất hiện trong câu hỏi lại: người dùng mở nhiều thẻ, phải biết
    // mình đang báo quán nào.
    expect(screen.getByText('Bún Ốc Hương Xưa')).toBeInTheDocument();
  });

  it('huỷ thì không gửi gì cả', async () => {
    renderNut();
    fireEvent.click(screen.getByRole('button', { name: /đã đóng cửa/i }));
    fireEvent.click(screen.getByRole('button', { name: /huỷ/i }));

    expect(logInteraction).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: /đã đóng cửa/i })).toBeInTheDocument();
  });

  it('xác nhận thì gửi đúng action_type và session_id', async () => {
    renderNut();
    fireEvent.click(screen.getByRole('button', { name: /đã đóng cửa/i }));
    fireEvent.click(screen.getByRole('button', { name: /đúng, đã đóng/i }));

    expect(logInteraction).toHaveBeenCalledWith(
      expect.objectContaining({
        restaurant_id: 'ChIJtest',
        action_type: 'report_closed',
        session_id: 'phien-test',
      }),
    );
    expect(await screen.findByText(/đã ghi nhận/i)).toBeInTheDocument();
  });

  it('KHÔNG hứa quán biến mất ngay, và không nhắc con số ngưỡng', async () => {
    // Ngưỡng ẩn quán là quy tắc NGHIỆP VỤ, chỉ được nằm ở backend. Viết lại con số ở đây
    // là tạo nơi thứ hai chứa cùng một luật (CLAUDE.md mục 1b).
    renderNut();
    fireEvent.click(screen.getByRole('button', { name: /đã đóng cửa/i }));
    fireEvent.click(screen.getByRole('button', { name: /đúng, đã đóng/i }));

    const loiCamOn = await screen.findByText(/đã ghi nhận/i);
    expect(loiCamOn.textContent).toMatch(/thêm người xác nhận/i);
    expect(loiCamOn.textContent).not.toMatch(/\d/);
  });

  it('gửi hỏng thì phải nói ra và cho thử lại', async () => {
    // `logInteraction` nuốt lỗi và trả null - đúng cho ghi log ngầm, nhưng ở đây người
    // dùng đang chủ động chờ phản hồi nên im lặng là nói dối.
    logInteraction.mockResolvedValue(null);
    renderNut();
    fireEvent.click(screen.getByRole('button', { name: /đã đóng cửa/i }));
    fireEvent.click(screen.getByRole('button', { name: /đúng, đã đóng/i }));

    expect(await screen.findByText(/gửi không được/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /thử lại/i })).toBeInTheDocument();
  });
});
