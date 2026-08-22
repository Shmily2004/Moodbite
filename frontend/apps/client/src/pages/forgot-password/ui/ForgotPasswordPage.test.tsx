/**
 * Trang QUÊN MẬT KHẨU (bước 1 — xin thư).
 *
 * Bước 2 test ở `pages/reset-password`: luật FSD cấm một page import page khác, kể cả
 * trong file test.
 *
 * Giả lập `fetch` ở mức thấp nhất để đi qua đúng lớp `HttpClient` thật: sai đường dẫn
 * endpoint hay sai tên trường (`new_password` chẳng hạn) là test đỏ ngay.
 */
import { describe, expect, it, vi, afterEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ForgotPasswordPage } from '../index';

const CAU_BACKEND =
  'Nếu tài khoản tồn tại và đã khai email, thư hướng dẫn đặt lại mật khẩu đã được gửi.';

function mockOk(message: string, status = 200) {
  return vi.fn().mockResolvedValue({
    ok: true,
    status,
    json: async () => ({ data: { message } }),
  });
}

function mockLoi(code: string, message: string, status: number) {
  return vi.fn().mockResolvedValue({
    ok: false,
    status,
    json: async () => ({ error: { code, message } }),
  });
}

function renderQuen() {
  return render(
    <MemoryRouter>
      <ForgotPasswordPage />
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('ForgotPasswordPage', () => {
  it('gọi đúng /auth/forgot-password với thứ người dùng gõ', async () => {
    const fetchMock = mockOk(CAU_BACKEND);
    vi.stubGlobal('fetch', fetchMock);
    renderQuen();

    fireEvent.change(screen.getByLabelText('Email hoặc tên đăng nhập'), {
      target: { value: '  Mung@vidu.com  ' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Gửi hướng dẫn đặt lại' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toContain('/auth/forgot-password');
    // Cắt khoảng trắng thừa (hay dính khi copy) nhưng KHÔNG tự hạ chữ thường — đó là việc
    // của backend, frontend đoán thêm chỉ tạo hai nơi cùng chuẩn hoá.
    expect(JSON.parse(init.body)).toEqual({ identifier: 'Mung@vidu.com' });
  });

  it('hiện ĐÚNG câu backend trả về, không tự viết câu khẳng định hơn', async () => {
    vi.stubGlobal('fetch', mockOk(CAU_BACKEND));
    renderQuen();

    fireEvent.change(screen.getByLabelText('Email hoặc tên đăng nhập'), {
      target: { value: 'mung' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Gửi hướng dẫn đặt lại' }));

    // Câu này cố tình mơ hồ ("nếu tài khoản tồn tại") để không lộ ai đã đăng ký.
    // Thay bằng "Đã gửi thư tới mung@..." là phá đúng chốt chặn đó.
    expect(await screen.findByRole('status')).toHaveTextContent('Nếu tài khoản tồn tại');
  });

  it('gửi xong thì ẨN ô nhập, không cho bấm gửi liên tục', async () => {
    vi.stubGlobal('fetch', mockOk(CAU_BACKEND));
    renderQuen();

    fireEvent.change(screen.getByLabelText('Email hoặc tên đăng nhập'), {
      target: { value: 'mung' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Gửi hướng dẫn đặt lại' }));

    await screen.findByRole('status');
    // Mỗi lần bấm là một lá thư thật, backend chỉ cho 3 lần/giờ.
    expect(screen.queryByLabelText('Email hoặc tên đăng nhập')).not.toBeInTheDocument();
  });

  it('bị chặn tần suất thì hiện đúng câu của backend', async () => {
    vi.stubGlobal(
      'fetch',
      mockLoi('RATE_LIMITED', 'Bạn thử hơi nhiều lần. Chờ 60 giây rồi thử lại.', 429),
    );
    renderQuen();

    fireEvent.change(screen.getByLabelText('Email hoặc tên đăng nhập'), {
      target: { value: 'mung' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Gửi hướng dẫn đặt lại' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Chờ 60 giây');
  });
});
