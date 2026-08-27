/**
 * SMOKE TEST cho app QUẢN TRỊ: render được + route/layout/chốt chặn đăng nhập đúng.
 *
 * App này trước đó có **0 test** — tức là màn hình trắng sẽ lọt qua CI mà không ai biết.
 * Đây đúng là lỗ hổng backend đã trả giá để học (CLAUDE.md mục 0): test xanh nhưng app
 * không chạy được, vì không test nào dựng app lên.
 *
 * Test dựng router từ mảng `routes` thật để vào thẳng từng đường dẫn, không cần trình
 * duyệt thật.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, useRoutes } from 'react-router-dom';
import { routes } from './routes';

const TOKEN_KEY = 'moodbite.admin.token';

/**
 * Dung `useRoutes` + `MemoryRouter` thay vi `createMemoryRouter`.
 *
 * VI SAO: data router cua react-router tao doi tuong `Request` moi lan dieu huong.
 * Trong jsdom, `AbortSignal` cua jsdom khong duoc `Request` cua Node (undici) chap nhan
 * -> moi test co chuyen huong deu no `TypeError: Expected signal to be an instance of
 * AbortSignal`. Loi cua MOI TRUONG TEST, khong phai cua app.
 *
 * `useRoutes` van dung CHINH mang `routes` that, nen van kiem duoc dang ky route.
 */
function Harness() {
  return useRoutes(routes);
}

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Harness />
    </MemoryRouter>,
  );
}

describe('App quan tri - smoke test', () => {
  let errorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    sessionStorage.clear();
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('backend tat')));
    errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    errorSpy.mockRestore();
    sessionStorage.clear();
  });

  it('render duoc, khong nem loi', () => {
    expect(() => renderAt('/login')).not.toThrow();
  });

  it('trang dang nhap hien day du o nhap - KHONG trang', () => {
    renderAt('/login');

    expect(screen.getByRole('heading', { name: /Quản trị/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Tên đăng nhập/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Mật khẩu/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Đăng nhập/i })).toBeInTheDocument();
  });
});

describe('Chot chan dang nhap (RequireAuth)', () => {
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

  it('chua dang nhap ma vao trang tong quan -> bi da ve /login', () => {
    renderAt('/');

    expect(screen.getByRole('button', { name: /Đăng nhập/i })).toBeInTheDocument();
    // Không được lộ nội dung trang quản trị.
    expect(screen.queryByText(/trung tâm vận hành/i)).not.toBeInTheDocument();
  });

  it('chua dang nhap ma vao trang quan an -> bi da ve /login', () => {
    renderAt('/quan-an');

    expect(screen.getByRole('button', { name: /Đăng nhập/i })).toBeInTheDocument();
    expect(screen.queryByText(/Quản lý quán/i)).not.toBeInTheDocument();
  });

  it('duong dan la KHI CHUA dang nhap cung bi da ve /login', () => {
    renderAt('/linh-tinh');

    expect(screen.getByRole('button', { name: /Đăng nhập/i })).toBeInTheDocument();
  });

  it('co token thi vao duoc, va trang dau tien la TONG QUAN', () => {
    // Chủ dự án hỏi thẳng 2026-08-26: "nhập tài khoản admin có hiện lên dashboard
    // không?". Test này khoá đúng câu trả lời — `/` phải là TỔNG QUAN, không phải bảng
    // 52.854 quán như trước.
    sessionStorage.setItem(TOKEN_KEY, 'token-gia-cho-test');

    renderAt('/');

    expect(screen.getByRole('heading', { name: /Tổng quan/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Xin chào, Admin/i })).toBeInTheDocument();
  });

  it('co token thi van vao duoc trang quan an o duong dan rieng', () => {
    sessionStorage.setItem(TOKEN_KEY, 'token-gia-cho-test');

    renderAt('/quan-an');

    // Xuất hiện HAI lần là ĐÚNG: h1 ở thanh trên (layout suy từ đường dẫn) và h2 của
    // chính trang. Kiểm theo cấp để nói rõ đang khẳng định cái nào.
    expect(screen.getByRole('heading', { level: 1, name: /Quản lý quán ăn/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: /Quản lý quán/i })).toBeInTheDocument();
  });
});

describe('Layout dung chung', () => {
  beforeEach(() => {
    sessionStorage.setItem(TOKEN_KEY, 'token-gia-cho-test');
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('backend tat')));
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    sessionStorage.clear();
  });

  it('da dang nhap thi thay khung: menu ben trai + nut dang xuat', () => {
    renderAt('/');

    expect(screen.getByRole('link', { name: /Quản lý quán ăn/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Đăng xuất/i })).toBeInTheDocument();
  });

  it('muc menu CHUA DUNG khong phai link - bam vao khong ra 404', () => {
    // "Chất lượng dữ liệu" là mục DUY NHẤT chưa dựng (chủ dự án chốt 2026-08-26).
    // Làm link chết thì người dùng bấm vào gặp 404 mà không hiểu vì sao.
    renderAt('/');

    expect(
      screen.queryByRole('link', { name: /Chất lượng dữ liệu/i }),
    ).not.toBeInTheDocument();
    expect(screen.getByText(/Chất lượng dữ liệu/i)).toBeInTheDocument();
  });

  it('sau mục còn lại đều là link that', () => {
    renderAt('/');

    for (const nhan of [
      /Tổng quan/i,
      /Quản lý món ăn/i,
      /Quản lý quán ăn/i,
      /Gợi ý & Hệ thống/i,
      /Nhật ký hoạt động/i,
      /Cài đặt hệ thống/i,
    ]) {
      expect(screen.getByRole('link', { name: nhan })).toBeInTheDocument();
    }
  });

  it.each([
    ['/mon-an', /Quản lý món ăn/i],
    ['/goi-y', /Gợi ý & Hệ thống/i],
    ['/nhat-ky', /Nhật ký hoạt động/i],
    ['/cai-dat', /Cài đặt hệ thống/i],
  ])('trang %s dung duoc va co tieu de tren thanh dau', (duongDan, ten) => {
    // Backend đang tắt trong test (fetch reject) — trang VẪN phải dựng được, không trắng.
    renderAt(duongDan);

    expect(screen.getByRole('heading', { level: 1, name: ten })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Đăng xuất/i })).toBeInTheDocument();
  });

  it('trang 404 VAN nam trong khung layout', () => {
    renderAt('/duong-dan-khong-ton-tai');

    expect(screen.getByText(/Không có trang này/i)).toBeInTheDocument();
    // Điểm chính của việc tách layout: khung dùng chung cho MỌI trang con.
    expect(screen.getByRole('button', { name: /Đăng xuất/i })).toBeInTheDocument();
  });

  it('da dang nhap ma mo /login thi bi day ve TONG QUAN', () => {
    renderAt('/login');

    expect(screen.getByRole('heading', { name: /Xin chào, Admin/i })).toBeInTheDocument();
  });
});
