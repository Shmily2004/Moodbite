/**
 * Test màn "Tổng quan": biểu đồ vành khuyên nguồn dữ liệu + khối "Hệ thống gợi ý".
 *
 * Canh: KHÔNG có CTR · 0 lượt tương tác thì trạng thái rỗng · kho hỏng khác "0 lượt".
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const { overview, activity, interactionStats } = vi.hoisted(() => ({
  overview: vi.fn(),
  activity: vi.fn(),
  interactionStats: vi.fn(),
}));

vi.mock('@/shared/api', async () => {
  const that = await vi.importActual<typeof import('@/shared/api')>('@/shared/api');
  return { ...that, adminApi: { overview, activity, interactionStats } };
});

import { OverviewPage } from './ui/OverviewPage';

function moTrang() {
  return render(
    <MemoryRouter>
      <OverviewPage />
    </MemoryRouter>,
  );
}

const TONG_QUAN = {
  restaurants_total: 52871,
  restaurants_visible: 52871,
  restaurants_hidden: 0,
  dishes_total: 855,
  dishes_with_restaurants: 298,
  dishes_without_restaurants: 557,
  interactions_total: 3,
  data_quality: [],
  by_source: [
    { source: 'overture', count: 48406, percent: 91.6 },
    { source: 'openstreetmap', count: 3025, percent: 5.7 },
    { source: 'google_maps_apify', count: 1440, percent: 2.7 },
  ],
  needs_attention: [],
  needs_attention_total: 16,
  generated_at: '2026-09-16T02:00:00+00:00',
};

function thongKe(ghiDe: Record<string, unknown> = {}) {
  return {
    available: true,
    total: 3,
    positive_rate: 100,
    sessions: 2,
    users: 1,
    by_action: [{ action_type: 'view_detail', count: 3 }],
    last_7_days: Array.from({ length: 7 }, (_, i) => ({
      date: `2026-09-${10 + i}`,
      count: i === 6 ? 3 : 0,
    })),
    ...ghiDe,
  };
}

beforeEach(() => {
  overview.mockResolvedValue(TONG_QUAN);
  activity.mockResolvedValue({ entries: [], total: 0, available: true });
  interactionStats.mockResolvedValue(thongKe());
  vi.spyOn(console, 'error').mockImplementation(() => {});
  vi.spyOn(console, 'warn').mockImplementation(() => {});
});

afterEach(() => {
  vi.clearAllMocks();
  vi.restoreAllMocks();
});

describe('Man "Tong quan"', () => {
  it('nguon du lieu ve vanh khuyen va GIU so + chu thich', async () => {
    moTrang();

    expect(
      await screen.findByRole('img', { name: /Tỷ lệ quán theo nguồn: Overture Maps 91.6%/ }),
    ).toBeInTheDocument();
    expect(screen.getByText('(48.406)')).toBeInTheDocument();
  });

  it('he thong goi y hien so that va KHONG co CTR', async () => {
    moTrang();

    expect(await screen.findByText('Tín hiệu tích cực')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Xem chi tiết hệ thống gợi ý/ })).toHaveAttribute(
      'href',
      '/goi-y',
    );
    expect(screen.queryByText(/^Tỷ lệ click/)).not.toBeInTheDocument();
    expect(screen.getByRole('img', { name: /Lượt tương tác 7 ngày/ })).toBeInTheDocument();
  });

  it('0 luot tuong tac thi trang thai rong', async () => {
    interactionStats.mockResolvedValue(
      thongKe({ total: 0, positive_rate: null, sessions: 0, users: 0, by_action: [] }),
    );
    moTrang();

    expect(await screen.findByText(/Chưa có lượt tương tác nào được ghi/)).toBeInTheDocument();
  });

  it('kho nhat ky hong thi noi ro, KHONG hien 0 luot', async () => {
    interactionStats.mockResolvedValue(thongKe({ available: false, total: 0 }));
    moTrang();

    expect(await screen.findByText(/Không đọc được nhật ký tương tác/)).toBeInTheDocument();
  });

  it('co link "Xem chi tiet" sang trang Can xu ly', async () => {
    moTrang();

    const link = await screen.findByRole('link', { name: 'Xem chi tiết →' });
    expect(link).toHaveAttribute('href', '/can-xu-ly');
  });
});
