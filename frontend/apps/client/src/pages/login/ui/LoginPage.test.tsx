/**
 * Trang đăng nhập phải NỐI THÔNG suốt: form -> hook -> HttpClient -> `/auth/login`,
 * rồi token đi vào đúng kho lưu trữ.
 *
 * Giả lập `fetch` ở mức thấp nhất (không mock module `@/shared/api`): như vậy test đi qua
 * ĐÚNG lớp `HttpClient` thật, nên nếu envelope `{data: ...}` hay đường dẫn endpoint bị
 * viết sai thì test đỏ — chứ không phải chỉ chứng minh "component render được".
 */
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
// `fireEvent` chứ không phải `user-event`: form này chỉ cần gõ chữ và bấm nút, thêm một
// gói npm nữa cho từng ấy việc là không đáng - cùng lý do với `ReportClosureButton.test`.
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { UserSessionProvider } from '@/entities/user';
import { LoginPage } from '../index';

const TOKEN = 'token-gia-lap';

/** Hình dạng ĐÚNG như backend trả (`AuthData`, bọc trong `data`). */
function mockLoginOk() {
  return vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({
      data: {
        user: { user_id: 'u1', username: 'mung', role: 'user', display_name: 'Mừng' },
        token: TOKEN,
        token_type: 'bearer',
        expires_in: 86400,
      },
    }),
  });
}

/** 401: backend cố tình KHÔNG nói sai tên hay sai mật khẩu. */
function mockLogin401() {
  return vi.fn().mockResolvedValue({
    ok: false,
    status: 401,
    json: async () => ({
      error: { code: 'UNAUTHORIZED', message: 'Sai tài khoản hoặc mật khẩu.' },
    }),
  });
}

function renderLogin() {
  return render(
    <MemoryRouter>
      <UserSessionProvider>
        <LoginPage />
      </UserSessionProvider>
    </MemoryRouter>,
  );
}

function dangNhap(remember = false) {
  fireEvent.change(screen.getByLabelText('Tên đăng nhập'), {
    target: { value: 'mung' },
  });
  fireEvent.change(screen.getByLabelText('Mật khẩu'), {
    target: { value: 'matkhaudai123' },
  });
  if (remember) fireEvent.click(screen.getByLabelText('Ghi nhớ đăng nhập'));
  fireEvent.click(screen.getByRole('button', { name: 'Đăng nhập' }));
}

describe('LoginPage', () => {
  beforeEach(() => {
    // Token sót lại từ test trước sẽ khiến trang chuyển hướng thay vì hiện form.
    localStorage.clear();
    sessionStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('dùng logo trong design/attribute, không phải logo vẽ lại', () => {
    vi.stubGlobal('fetch', vi.fn());
    renderLogin();

    // Chốt chặn cho quy ước "logo ở attribute mới là bản đúng" (chủ dự án 2026-08-21).
    expect(screen.getByAltText('MoodBite')).toHaveAttribute('src', '/anh/logo.png');
  });

  it('gọi đúng /auth/login và lưu token vào sessionStorage khi KHÔNG ghi nhớ', async () => {
    const fetchMock = mockLoginOk();
    vi.stubGlobal('fetch', fetchMock);
    renderLogin();

    dangNhap();

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toContain('/auth/login');
    expect(JSON.parse(init.body)).toEqual({
      username: 'mung',
      password: 'matkhaudai123',
    });

    await waitFor(() => {
      expect(sessionStorage.getItem('moodbite.user.token')).toBe(TOKEN);
    });
    // Không tick "ghi nhớ" thì TUYỆT ĐỐI không được đọng lại ở localStorage.
    expect(localStorage.getItem('moodbite.user.token')).toBeNull();
  });

  it('lưu token vào localStorage khi có tick "Ghi nhớ đăng nhập"', async () => {
    vi.stubGlobal('fetch', mockLoginOk());
    renderLogin();

    dangNhap(true);

    await waitFor(() => {
      expect(localStorage.getItem('moodbite.user.token')).toBe(TOKEN);
    });
    expect(sessionStorage.getItem('moodbite.user.token')).toBeNull();
  });

  it('hiện ĐÚNG câu lỗi của backend khi sai mật khẩu', async () => {
    vi.stubGlobal('fetch', mockLogin401());
    renderLogin();

    dangNhap();

    // Không được hiện "Phiên đăng nhập đã hết hạn" - đó là câu soạn sẵn cho luồng tìm
    // quán, đọc vào là hiểu sai hoàn toàn nguyên nhân.
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Sai tài khoản hoặc mật khẩu.',
    );
    expect(sessionStorage.getItem('moodbite.user.token')).toBeNull();
  });

  it('nút con mắt đổi ô mật khẩu qua lại giữa che và hiện', () => {
    vi.stubGlobal('fetch', vi.fn());
    renderLogin();

    const oMatKhau = screen.getByLabelText('Mật khẩu');
    expect(oMatKhau).toHaveAttribute('type', 'password');

    fireEvent.click(screen.getByRole('button', { name: 'Hiện mật khẩu' }));
    expect(oMatKhau).toHaveAttribute('type', 'text');

    fireEvent.click(screen.getByRole('button', { name: 'Ẩn mật khẩu' }));
    expect(oMatKhau).toHaveAttribute('type', 'password');
  });
});
