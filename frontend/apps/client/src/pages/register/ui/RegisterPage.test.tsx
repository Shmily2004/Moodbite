/**
 * Trang đăng ký phải NỐI THÔNG suốt: form -> phiên tài khoản -> `/auth/register`.
 *
 * Giả lập `fetch` ở mức thấp nhất (không mock module `@/shared/api`) để test đi qua ĐÚNG
 * lớp `HttpClient` thật — sai tên trường hay sai đường dẫn endpoint là test đỏ ngay.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { UserSessionProvider } from '@/entities/user';
import { RegisterPage } from '../index';

const TOKEN = 'token-gia-lap';

function mockRegisterOk() {
  return vi.fn().mockResolvedValue({
    ok: true,
    status: 201,
    json: async () => ({
      data: {
        user: { user_id: 'u9', username: 'mung', role: 'user', display_name: 'Mừng' },
        token: TOKEN,
        token_type: 'bearer',
        expires_in: 86400,
      },
    }),
  });
}

/** 409: tên đã có người dùng. Câu chữ do backend quyết. */
function mockRegister409() {
  return vi.fn().mockResolvedValue({
    ok: false,
    status: 409,
    json: async () => ({
      error: { code: 'USERNAME_TAKEN', message: 'Tên đăng nhập này đã có người dùng.' },
    }),
  });
}

function renderRegister() {
  return render(
    <MemoryRouter>
      <UserSessionProvider>
        <RegisterPage />
      </UserSessionProvider>
    </MemoryRouter>,
  );
}

interface DienOptions {
  displayName?: string;
  password?: string;
  confirm?: string;
}

function dienForm({
  displayName = 'Mừng',
  password = 'matkhaudai123',
  confirm = 'matkhaudai123',
}: DienOptions = {}) {
  fireEvent.change(screen.getByLabelText('Tên đăng nhập'), {
    target: { value: 'mung' },
  });
  fireEvent.change(screen.getByLabelText('Tên hiển thị'), {
    target: { value: displayName },
  });
  fireEvent.change(screen.getByLabelText('Mật khẩu'), { target: { value: password } });
  fireEvent.change(screen.getByLabelText('Xác nhận mật khẩu'), {
    target: { value: confirm },
  });
  fireEvent.click(screen.getByLabelText(/Tôi đồng ý/));
  fireEvent.click(screen.getByRole('button', { name: 'Tạo tài khoản' }));
}

describe('RegisterPage', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('gửi đúng /auth/register và lưu token của phiên mới', async () => {
    const fetchMock = mockRegisterOk();
    vi.stubGlobal('fetch', fetchMock);
    renderRegister();

    dienForm();

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toContain('/auth/register');
    expect(JSON.parse(init.body)).toEqual({
      username: 'mung',
      password: 'matkhaudai123',
      display_name: 'Mừng',
    });

    await waitFor(() => {
      expect(sessionStorage.getItem('moodbite.user.token')).toBe(TOKEN);
    });
  });

  it('bỏ trống tên hiển thị thì gửi null, KHÔNG gửi chuỗi rỗng', async () => {
    const fetchMock = mockRegisterOk();
    vi.stubGlobal('fetch', fetchMock);
    renderRegister();

    dienForm({ displayName: '   ' });

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(JSON.parse(fetchMock.mock.calls[0][1].body).display_name).toBeNull();
  });

  it('hai ô mật khẩu lệch nhau thì KHÔNG gọi API', async () => {
    const fetchMock = mockRegisterOk();
    vi.stubGlobal('fetch', fetchMock);
    renderRegister();

    dienForm({ confirm: 'gothieumotchu' });

    expect(await screen.findByRole('alert')).toHaveTextContent('chưa giống nhau');
    // Đây là điểm chính: biết chắc sai thì đừng làm phiền server.
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('hiện đúng câu lỗi của backend khi tên đã có người dùng', async () => {
    vi.stubGlobal('fetch', mockRegister409());
    renderRegister();

    dienForm();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Tên đăng nhập này đã có người dùng.',
    );
    expect(sessionStorage.getItem('moodbite.user.token')).toBeNull();
  });

  it('dùng tranh nền riêng của trang đăng ký', () => {
    vi.stubGlobal('fetch', vi.fn());
    const { container } = renderRegister();

    // Tranh nền là `background-image` chứ không phải thẻ <img> — xem AuthLayout.
    const tranh = container.querySelector<HTMLElement>('.auth__scene');
    expect(tranh?.style.backgroundImage).toContain('/anh/nen-dang-ky.png');
  });
});
