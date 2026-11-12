/**
 * Khối "Quán bị khách báo đóng cửa" — hàng chờ UC21. Khoá: hiện đúng số người báo + trạng
 * thái do backend trả; "Ẩn quán" và "Gỡ lượt báo" gọi đúng API rồi TẢI LẠI (không tự suy
 * is_hidden). Không còn ngưỡng ẩn tự động (biểu đồ UC06).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';

const closureReports = vi.fn();
const clearClosureReports = vi.fn();
const hideRestaurant = vi.fn();

vi.mock('@admin/shared/api', async () => {
  const that = await vi.importActual<typeof import('@admin/shared/api')>('@admin/shared/api');
  return {
    ...that,
    adminApi: {
      closureReports: (...a: unknown[]) => closureReports(...a),
      clearClosureReports: (...a: unknown[]) => clearClosureReports(...a),
      hideRestaurant: (...a: unknown[]) => hideRestaurant(...a),
    },
  };
});

import { ApiError } from '@admin/shared/api';
import { ClosureReportsPanel } from './ClosureReportsPanel';

beforeEach(() => {
  closureReports.mockReset();
  clearClosureReports.mockReset();
  hideRestaurant.mockReset();
});

describe('ClosureReportsPanel', () => {
  it('hiện quán bị báo, số người báo và trạng thái ẩn do backend trả', async () => {
    closureReports.mockResolvedValue({
      items: [
        { restaurant_id: 'p1', name: 'Phở Thìn', report_count: 3, is_hidden: true },
        { restaurant_id: 'p2', name: null, report_count: 1, is_hidden: false },
      ],
    });

    render(<ClosureReportsPanel />);

    expect(await screen.findByText('Phở Thìn')).toBeInTheDocument();
    expect(screen.getByText('Đang bị ẩn')).toBeInTheDocument();
    expect(screen.getByText('Chờ xử lý')).toBeInTheDocument();
    // Quán đã bị xoá khỏi dữ liệu: hiện mã thay cho tên, không hiện "null".
    expect(screen.getByText('p2')).toBeInTheDocument();
    // Quán đã bị ẩn không còn nút "Ẩn quán"; quán chờ xử lý thì có.
    expect(screen.getByRole('button', { name: /Ẩn quán p2/ })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Ẩn quán Phở Thìn/ })).not.toBeInTheDocument();
  });

  it('bấm "Ẩn quán" (quán thật sự đã đóng) gọi API ẩn rồi tải lại', async () => {
    closureReports
      .mockResolvedValueOnce({
        items: [{ restaurant_id: 'p2', name: 'Bún Chả', report_count: 2, is_hidden: false }],
      })
      .mockResolvedValueOnce({
        items: [{ restaurant_id: 'p2', name: 'Bún Chả', report_count: 2, is_hidden: true }],
      });
    hideRestaurant.mockResolvedValue({});

    render(<ClosureReportsPanel />);
    fireEvent.click(await screen.findByRole('button', { name: /Ẩn quán Bún Chả/ }));

    await waitFor(() => expect(hideRestaurant).toHaveBeenCalledWith('p2'));
    expect(await screen.findByText('Đang bị ẩn')).toBeInTheDocument();
    expect(closureReports).toHaveBeenCalledTimes(2);
  });

  it('bấm "Gỡ lượt báo" gọi đúng API rồi tải lại danh sách', async () => {
    closureReports
      .mockResolvedValueOnce({
        items: [{ restaurant_id: 'p1', name: 'Phở Thìn', report_count: 3, is_hidden: false }],
      })
      .mockResolvedValueOnce({ items: [] });
    clearClosureReports.mockResolvedValue({ restaurant_id: 'p1', cleared_reports: 3, is_hidden: false });

    render(<ClosureReportsPanel />);
    fireEvent.click(await screen.findByRole('button', { name: /Gỡ lượt báo đóng cửa của Phở Thìn/ }));

    await waitFor(() => expect(clearClosureReports).toHaveBeenCalledWith('p1'));
    expect(await screen.findByText('Chưa có quán nào bị khách báo đóng cửa.')).toBeInTheDocument();
    expect(closureReports).toHaveBeenCalledTimes(2);
  });

  it('lỗi thì hiện đúng câu backend, không giả vờ "không có quán nào"', async () => {
    closureReports.mockRejectedValue(
      new ApiError('DATA_NOT_READY', 'Không mở được nhật ký tương tác.', {}, 503),
    );

    render(<ClosureReportsPanel />);

    expect(await screen.findByText('Không mở được nhật ký tương tác.')).toBeInTheDocument();
    expect(screen.queryByText('Chưa có quán nào bị khách báo đóng cửa.')).not.toBeInTheDocument();
  });
});
