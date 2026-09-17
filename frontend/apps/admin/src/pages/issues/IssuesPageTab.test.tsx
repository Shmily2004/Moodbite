/**
 * Test phần bổ sung 2026-09-16 của màn "Cần xử lý": tab "Đã xử lý (N)", lọc theo loại,
 * cột "Xử lý gần nhất", nút "Xuất danh sách".
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { mocVanDe } from '@/shared/test';

const { issues, issueDetail, resolvedIssues } = vi.hoisted(() => ({
  issues: vi.fn(),
  issueDetail: vi.fn(),
  resolvedIssues: vi.fn(),
}));

vi.mock('@/shared/api', async () => {
  const that = await vi.importActual<typeof import('@/shared/api')>('@/shared/api');
  return { ...that, adminApi: { issues, issueDetail, resolvedIssues } };
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
  resolvedIssues.mockResolvedValue({
    total: 1,
    results: [
      {
        key: 'mon_thieu_anh',
        group_label: 'Món chưa có ảnh',
        target_type: 'mon_an',
        target_id: 'kem-bo',
        name: null,
        resolved_by: 'admin',
        note: null,
        resolved_at: '2026-09-15T02:00:00+00:00',
      },
    ],
  });
  vi.spyOn(console, 'error').mockImplementation(() => {});
  vi.spyOn(console, 'warn').mockImplementation(() => {});
});

afterEach(() => {
  vi.clearAllMocks();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe('Man "Can xu ly" - phan bo sung', () => {
  it('tab "Da xu ly" dem tu resolved_total va chi tai khi duoc mo', async () => {
    moTrang();
    const tab = await screen.findByRole('button', { name: 'Đã xử lý (12)' });
    expect(resolvedIssues).not.toHaveBeenCalled();

    fireEvent.click(tab);

    // Không tra được tên -> hiện MÃ bản ghi, không bịa tên.
    expect(await screen.findByText('kem-bo')).toBeInTheDocument();
    expect(screen.getByText('Món chưa có ảnh')).toBeInTheDocument();
  });

  it('loc theo loai van de chi con nhom dung loai', async () => {
    moTrang();
    await screen.findByText('Quán có khả năng đã đóng cửa');

    fireEvent.change(screen.getByRole('combobox', { name: /Lọc theo loại vấn đề/ }), {
      target: { value: 'mon_an' },
    });

    expect(screen.queryByText('Quán có khả năng đã đóng cửa')).not.toBeInTheDocument();
    expect(screen.getByText('Món chưa có ảnh')).toBeInTheDocument();
  });

  it('cot "Xu ly gan nhat" hien "—" khi chua ai danh dau', async () => {
    moTrang();
    await screen.findByText('Quán có khả năng đã đóng cửa');

    expect(screen.getByRole('columnheader', { name: /Xử lý gần nhất/ })).toBeInTheDocument();
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });

  it('xuat danh sach tao file CSV tu du lieu dang hien', async () => {
    const taoUrl = vi.fn(() => 'blob:gia');
    vi.stubGlobal('URL', Object.assign(URL, { createObjectURL: taoUrl, revokeObjectURL: vi.fn() }));
    const bam = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});

    moTrang();
    await screen.findByText('Quán có khả năng đã đóng cửa');
    fireEvent.click(screen.getByRole('button', { name: /Xuất danh sách/ }));

    await waitFor(() => expect(bam).toHaveBeenCalled());
    const blob = (taoUrl.mock.calls[0] as unknown as [Blob])[0];
    // `Blob.text()` chưa có trong jsdom — đọc bằng FileReader.
    const chu = await new Promise<string>((xong) => {
      const doc = new FileReader();
      doc.onload = () => xong(String(doc.result));
      doc.readAsText(blob);
    });
    expect(chu).toContain('Vấn đề,Mô tả,Loại,Độ ưu tiên,Số lượng,Xử lý gần nhất');
    expect(chu).toContain('Quán có khả năng đã đóng cửa');
  });
});
