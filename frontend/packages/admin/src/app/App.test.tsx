/**
 * Test KHU QUẢN TRỊ sau khi gộp vào app người dùng (2026-11-01).
 *
 * Dựng router từ mảng `quanTriRoutes` thật, có thêm một route `/login` giả để kiểm việc
 * "chưa đăng nhập thì bị đá về trang đăng nhập chung" mà không cần cả app khách.
 *
 * Dùng `useRoutes` + `MemoryRouter` thay vì `createMemoryRouter`: data router tạo đối tượng
 * `Request`, và trong jsdom `AbortSignal` không khớp với Node (lỗi của MÔI TRƯỜNG test).
 */
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, useRoutes } from 'react-router-dom';
import { quanTriRoutes } from './routes';

const TOKEN_KEY = 'moodbite.admin.token';

function Harness() {
  return useRoutes([
    ...quanTriRoutes,
    { path: '/login', element: <p>TRANG-DANG-NHAP-CHUNG</p> },
  ]);
}

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Harness />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  sessionStorage.clear();
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('backend tat')));
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  sessionStorage.clear();
});

describe('Chốt chặn đăng nhập của khu quản trị (RequireAuth)', () => {
  it('chưa có phiên quản trị mà vào /quan-tri -> bị đá về trang đăng nhập chung', () => {
    renderAt('/quan-tri');

    expect(screen.getByText('TRANG-DANG-NHAP-CHUNG')).toBeInTheDocument();
    expect(screen.queryByText(/trung tâm vận hành/i)).not.toBeInTheDocument();
  });

  it('chưa có phiên quản trị mà vào trang quán -> bị đá về trang đăng nhập chung', () => {
    renderAt('/quan-tri/quan-an');

    expect(screen.getByText('TRANG-DANG-NHAP-CHUNG')).toBeInTheDocument();
  });

  it('có phiên quản trị thì vào được, và trang đầu tiên là TỔNG QUAN', () => {
    // Khoá đúng câu trả lời của chủ dự án (2026-08-26): đăng nhập xong vào Tổng quan,
    // không phải bảng 52.854 quán.
    sessionStorage.setItem(TOKEN_KEY, 'token-gia-cho-test');

    renderAt('/quan-tri');

    expect(screen.getByRole('heading', { name: /Tổng quan/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Xin chào, Admin/i })).toBeInTheDocument();
  });

  it('có phiên quản trị thì vào được trang quán ở đường dẫn riêng', () => {
    sessionStorage.setItem(TOKEN_KEY, 'token-gia-cho-test');

    renderAt('/quan-tri/quan-an');

    // Hai h1 không được trùng nhau: h1 ở thanh trên và h2 của chính trang.
    expect(screen.getByRole('heading', { level: 1, name: /Quản lý quán ăn/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: /Quản lý quán/i })).toBeInTheDocument();
  });
});

describe('Khung dùng chung của khu quản trị', () => {
  beforeEach(() => {
    sessionStorage.setItem(TOKEN_KEY, 'token-gia-cho-test');
  });

  it('đã đăng nhập thì thấy khung: menu bên trái và nút đăng xuất', () => {
    renderAt('/quan-tri');

    expect(screen.getByRole('link', { name: /Quản lý quán ăn/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Đăng xuất/i })).toBeInTheDocument();
  });

  it('không còn mục menu nào ở trạng thái CHƯA DỰNG', () => {
    renderAt('/quan-tri');

    expect(screen.queryByText(/chưa dựng/i)).not.toBeInTheDocument();
  });

  it('cả tám mục menu đều là link thật', () => {
    renderAt('/quan-tri');

    for (const nhan of [
      /Tổng quan/i,
      /Quản lý món ăn/i,
      /Quản lý quán ăn/i,
      /Chất lượng dữ liệu/i,
      /Cần xử lý/i,
      /Gợi ý & Hệ thống/i,
      /Nhật ký hoạt động/i,
      /Cài đặt hệ thống/i,
    ]) {
      expect(screen.getByRole('link', { name: nhan })).toBeInTheDocument();
    }
  });

  it.each([
    ['/quan-tri/mon-an', /Quản lý món ăn/i],
    ['/quan-tri/goi-y', /Gợi ý & Hệ thống/i],
    ['/quan-tri/nhat-ky', /Nhật ký hoạt động/i],
    ['/quan-tri/cai-dat', /Cài đặt hệ thống/i],
    ['/quan-tri/chat-luong', /Chất lượng dữ liệu/i],
    ['/quan-tri/can-xu-ly', /Cần xử lý/i],
  ])('trang %s dựng được và có tiêu đề trên thanh đầu', (duongDan, ten) => {
    // Backend tắt trong test (fetch lỗi) — trang vẫn phải dựng được, không trắng.
    renderAt(duongDan);

    expect(screen.getByRole('heading', { level: 1, name: ten })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Đăng xuất/i })).toBeInTheDocument();
  });

  it('trang 404 VẪN nằm trong khung layout', () => {
    renderAt('/quan-tri/duong-dan-khong-ton-tai');

    expect(screen.getByText(/Không có trang này/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Đăng xuất/i })).toBeInTheDocument();
  });
});
