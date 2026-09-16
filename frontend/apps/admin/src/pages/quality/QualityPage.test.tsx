/**
 * Test màn "CHẤT LƯỢNG DỮ LIỆU".
 *
 * TRỌNG TÂM KHÔNG PHẢI "TRANG CÓ RENDER KHÔNG" — `app/App.test.tsx` đã canh chuyện đó.
 * Ở đây canh thứ nguy hiểm hơn: **hiện một con số nghe hợp lý nhưng không có thật**.
 * Đây là màn dùng để KIỂM TRA dữ liệu, nên bịa số ngay trên nó là kiểu sai tệ nhất có
 * thể (CLAUDE.md mục 0 và mục 4).
 *
 *   - chưa có mốc so sánh -> phải nói "chưa đủ dữ liệu", KHÔNG hiện "+0" hay mũi tên
 *   - mới 1 ngày lịch sử  -> KHÔNG vẽ đường (một điểm trông y như "cả tuần không đổi")
 *   - kho lịch sử hỏng    -> nói rõ, không để biểu đồ trống trông như "không có vấn đề"
 */
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { mocChatLuong } from '@/shared/test';

// `vi.hoisted` là BẮT BUỘC: `vi.mock` được nâng lên đầu file, nên một `const` thường
// khai ở đây sẽ chưa khởi tạo lúc factory chạy ("Cannot access before initialization").
const { dataQuality, activity } = vi.hoisted(() => ({
  dataQuality: vi.fn(),
  activity: vi.fn(),
}));

// Chặn ở lớp `shared/api` — ranh giới thật giữa trang và mạng. Chặn `fetch` thay vào đó
// sẽ bắt test dựng lại envelope `{data: …}` bằng tay, rồi hỏng mỗi lần đổi cách bọc
// response dù trang không đổi gì.
vi.mock('@/shared/api', async () => {
  const that = await vi.importActual<typeof import('@/shared/api')>('@/shared/api');
  return { ...that, adminApi: { dataQuality, activity } };
});

import { QualityPage } from './ui/QualityPage';

function moTrang() {
  return render(
    <MemoryRouter>
      <QualityPage />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  dataQuality.mockResolvedValue(mocChatLuong());
  activity.mockResolvedValue({ entries: [], total: 0, available: true });
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  vi.clearAllMocks();
  vi.restoreAllMocks();
});

describe('Man "Chat luong du lieu"', () => {
  it('chua co moc thi noi "chua du du lieu" chu KHONG hien +0', async () => {
    moTrang();

    // Hai thẻ có mốc so sánh: tổng quán và tổng món.
    expect(await screen.findAllByText(/Chưa đủ dữ liệu để so sánh/i)).toHaveLength(2);
    expect(screen.queryByText(/↗/)).not.toBeInTheDocument();
    expect(screen.queryByText(/\+0/)).not.toBeInTheDocument();
  });

  it('co moc thi hien chenh lech that', async () => {
    dataQuality.mockResolvedValue(
      mocChatLuong({
        restaurants_total: {
          current: 52871,
          baseline: 52800,
          baseline_date: '2026-08-01',
          delta: 71,
        },
      }),
    );

    moTrang();

    expect(await screen.findByText(/↗ \+71 so với/)).toBeInTheDocument();
  });

  it('moi 1 ngay lich su thi KHONG ve duong, va noi ro vi sao', async () => {
    moTrang();

    expect(
      await screen.findByText(/Biểu đồ cần ít nhất 2 ngày để vẽ được xu hướng/i),
    ).toBeInTheDocument();
  });

  it('du 2 ngay thi ve duong', async () => {
    const goc = mocChatLuong();
    dataQuality.mockResolvedValue({
      ...goc,
      trend: [{ ...goc.trend[0], date: '2026-09-07' }, goc.trend[0]],
    });

    moTrang();

    expect(
      await screen.findByRole('img', { name: /Xu hướng vấn đề trong 2 ngày/i }),
    ).toBeInTheDocument();
  });

  it('kho lich su hong thi noi ro, KHONG im lang de bieu do trong', async () => {
    dataQuality.mockResolvedValue(mocChatLuong({ history_available: false, trend: [] }));

    moTrang();

    expect(await screen.findByText(/Không mở được kho lịch sử/i)).toBeInTheDocument();
  });

  it('backend tat thi VAN hien tieu de va nut lam moi - khong trang man', async () => {
    dataQuality.mockRejectedValue(new Error('backend tat'));

    moTrang();

    expect(
      screen.getByRole('heading', { name: /Chất lượng dữ liệu/i }),
    ).toBeInTheDocument();
    expect(await screen.findByText(/backend tat/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Làm mới/i })).toBeInTheDocument();
  });
});
