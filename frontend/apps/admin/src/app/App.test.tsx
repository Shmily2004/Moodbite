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

  it('chua dang nhap ma vao trang quan ly -> bi da ve /login', () => {
    renderAt('/');

    expect(screen.getByRole('button', { name: /Đăng nhập/i })).toBeInTheDocument();
    // Không được lộ nội dung trang quản trị.
    expect(screen.queryByText(/Quản lý quán/i)).not.toBeInTheDocument();
  });

  it('duong dan la KHI CHUA dang nhap cung bi da ve /login', () => {
    renderAt('/linh-tinh');

    expect(screen.getByRole('button', { name: /Đăng nhập/i })).toBeInTheDocument();
  });

  it('co token thi vao duoc trang quan ly', () => {
    sessionStorage.setItem(TOKEN_KEY, 'token-gia-cho-test');

    renderAt('/');

    expect(screen.getByRole('heading', { name: /Quản lý quán/i })).toBeInTheDocument();
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

  it('da dang nhap thi thay khung: dieu huong + nut dang xuat', () => {
    renderAt('/');

    expect(screen.getByRole('link', { name: /Quán ăn/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Đăng xuất/i })).toBeInTheDocument();
  });

  it('trang 404 VAN nam trong khung layout', () => {
    renderAt('/duong-dan-khong-ton-tai');

    expect(screen.getByText(/Không có trang này/i)).toBeInTheDocument();
    // Điểm chính của việc tách layout: khung dùng chung cho MỌI trang con.
    expect(screen.getByRole('button', { name: /Đăng xuất/i })).toBeInTheDocument();
  });

  it('da dang nhap ma mo /login thi bi day ve trang quan ly', () => {
    renderAt('/login');

    expect(screen.getByRole('heading', { name: /Quản lý quán/i })).toBeInTheDocument();
  });
});
