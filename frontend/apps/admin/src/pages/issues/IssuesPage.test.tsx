/**
 * Test màn "CẦN XỬ LÝ".
 *
 * Canh ba thứ dễ sai nhất, đều là kiểu sai "nhìn thì hợp lý":
 *
 *   - đổi tab lọc -> năm thẻ số phải GIỮ NGUYÊN (chúng tính trên toàn bộ dữ liệu)
 *   - nhóm 0 bản ghi -> VẪN hiện dòng, nhưng không mở được một danh sách rỗng
 *   - kho đánh dấu hỏng -> nói rõ, không để nút bấm hụt
 */
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { mocVanDe } from '@/shared/test';

// Xem ghi chú `vi.hoisted` ở `pages/quality/QualityPage.test.tsx`.
const { issues, issueDetail } = vi.hoisted(() => ({
  issues: vi.fn(),
  issueDetail: vi.fn(),
}));

vi.mock('@/shared/api', async () => {
  const that = await vi.importActual<typeof import('@/shared/api')>('@/shared/api');
  return { ...that, adminApi: { issues, issueDetail } };
});

import { IssuesPage } from './ui/IssuesPage';

function moTrang() {
  return render(
    <MemoryRouter>
      <IssuesPage />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  issues.mockResolvedValue(mocVanDe());
  issueDetail.mockResolvedValue({ key: 'dong_tam', total: 0, results: [] });
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  vi.clearAllMocks();
  vi.restoreAllMocks();
});

describe('Man "Can xu ly"', () => {
  it('hien du nam the so', async () => {
    moTrang();

    // Đọc TRONG danh sách thẻ số. Quét cả trang thì "Nghiêm trọng" khớp cả nút tab lẫn
    // nhãn ưu tiên trong bảng — ba chỗ khác nhau, và test sẽ xanh vì nhầm chỗ.
    const the = within(await screen.findByRole('list', { name: /Tổng hợp vấn đề/i }));

    for (const nhan of [
      'Nghiêm trọng',
      'Quan trọng',
      'Cần kiểm tra',
      'Đã xử lý hôm nay',
      'Tổng số vấn đề',
    ]) {
      expect(the.getByText(nhan)).toBeInTheDocument();
    }
  });

  it('doi tab loc thi nam the so GIU NGUYEN', async () => {
    // Backend trả bộ đếm toàn cục kể cả khi có `priority`. Nếu trang tự cộng lại từ
    // `groups` đã lọc thì bấm tab "Nghiêm trọng" sẽ làm ba thẻ kia tụt về 0 — người
    // quản trị sẽ tưởng vừa xử lý xong mọi thứ khác.
    moTrang();
    await screen.findByRole('list', { name: /Tổng hợp vấn đề/i });

    issues.mockResolvedValue(mocVanDe({ groups: [mocVanDe().groups[0]] }));
    fireEvent.click(screen.getByRole('button', { name: /^Nghiêm trọng \(16\)$/ }));

    await waitFor(() =>
      expect(issues).toHaveBeenLastCalledWith({ priority: 'nghiem_trong' }),
    );
    // 8.920 = thẻ "Quan trọng", vẫn đúng con số toàn cục.
    expect(screen.getByText('8.920')).toBeInTheDocument();
  });

  it('khong mo duoc kho danh dau thi noi ro thay vi de nut bam hut', async () => {
    issues.mockResolvedValue(mocVanDe({ can_resolve: false }));

    moTrang();

    expect(
      await screen.findByText(/Không mở được kho đánh dấu xử lý/i),
    ).toBeInTheDocument();
  });

  it('nhom 0 ban ghi VAN hien dong nhung khong mo duoc danh sach rong', async () => {
    issues.mockResolvedValue(
      mocVanDe({
        groups: [
          {
            key: 'trung_lap',
            label: 'Dữ liệu trùng lặp cần kiểm tra',
            description: 'Cùng tên và cùng vị trí',
            count: 0,
            severity: 'canh_bao',
            priority: 'quan_trong',
            target_type: 'du_lieu',
          },
        ],
      }),
    );

    moTrang();

    // Dòng vẫn hiện: "0 bản ghi trùng lặp" là câu trả lời có ích ("đã kiểm, không có
    // gì"), khác hẳn với việc dòng đó biến mất.
    expect(await screen.findByText(/Dữ liệu trùng lặp cần kiểm tra/i)).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /Xem danh sách/i }),
    ).not.toBeInTheDocument();
  });

  it('mo mot nhom thi hien ban ghi cu the, dong da xong van HIEN', async () => {
    issueDetail.mockResolvedValue({
      key: 'dong_tam',
      total: 2,
      results: [
        {
          key: 'dong_tam',
          id: 'q1',
          name: 'Phở Thìn',
          description: 'Hai Bà Trưng',
          image_url: null,
          source_updated_at: null,
          resolved_at: '2026-09-08T01:00:00+00:00',
          resolved_by: 'admin',
        },
        {
          key: 'dong_tam',
          id: 'q2',
          name: 'Bún Chả Hương Liên',
          description: 'Hai Bà Trưng',
          image_url: null,
          source_updated_at: null,
          resolved_at: null,
          resolved_by: null,
        },
      ],
    });

    moTrang();
    // Hai nhóm đều có bản ghi nên có hai nút; bấm nút của nhóm ĐẦU (`dong_tam`) —
    // đúng nhóm mà `issueDetail` đang giả lập.
    const nut = await screen.findAllByRole('button', { name: /Xem danh sách/i });
    fireEvent.click(nut[0]);

    // Dòng ĐÃ đánh dấu vẫn hiện — giấu đi thì người bấm nhầm không tìm lại được để gỡ.
    expect(await screen.findByText('Phở Thìn')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Gỡ đánh dấu/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Đánh dấu đã xử lý/i })).toBeInTheDocument();
  });

  it('backend tat thi VAN hien tieu de - khong trang man', async () => {
    issues.mockRejectedValue(new Error('backend tat'));

    moTrang();

    expect(screen.getByRole('heading', { name: /Cần xử lý/i })).toBeInTheDocument();
    expect(await screen.findByText(/backend tat/i)).toBeInTheDocument();
  });
});
