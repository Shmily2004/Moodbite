/**
 * Trang ĐẶT MẬT KHẨU MỚI (bước 2 của quên mật khẩu).
 *
 * File RIÊNG chứ không test chung với trang quên mật khẩu: luật FSD cấm một page import
 * page khác, kể cả trong file test — `steiger` bắt đúng lỗi này ở bản đầu.
 *
 * Giả lập `fetch` ở mức thấp nhất để đi qua đúng lớp `HttpClient` thật: sai đường dẫn hay
 * sai tên trường (`new_password` chẳng hạn) là test đỏ ngay.
 */
import { describe, expect, it, vi, afterEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ResetPasswordPage } from '../index';

function mockOk(message: string) {
  return vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
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

/** `duongDan` chứa cả query string, đúng như khi bấm link trong thư. */
function renderDatLai(duongDan = '/dat-lai-mat-khau?token=token-trong-thu') {
  return render(
    <MemoryRouter initialEntries={[duongDan]}>
      <ResetPasswordPage />
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('ResetPasswordPage', () => {
  it('đọc token từ query string và gửi kèm mật khẩu mới', async () => {
    const fetchMock = mockOk('Đã đổi mật khẩu. Hãy đăng nhập bằng mật khẩu mới.');
    vi.stubGlobal('fetch', fetchMock);
    renderDatLai();

    fireEvent.change(screen.getByLabelText('Mật khẩu mới'), {
      target: { value: 'mat-khau-moi-123' },
    });
    fireEvent.change(screen.getByLabelText('Xác nhận mật khẩu'), {
      target: { value: 'mat-khau-moi-123' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Đổi mật khẩu' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toContain('/auth/reset-password');
    expect(JSON.parse(init.body)).toEqual({
      token: 'token-trong-thu',
      new_password: 'mat-khau-moi-123',
    });
  });

  it('thiếu token trong đường dẫn thì KHÔNG cho gõ gì cả', () => {
    vi.stubGlobal('fetch', vi.fn());
    renderDatLai('/dat-lai-mat-khau');

    expect(screen.getByRole('alert')).toHaveTextContent('thiếu mã đặt lại');
    expect(screen.queryByLabelText('Mật khẩu mới')).not.toBeInTheDocument();
  });

  it('hai ô mật khẩu lệch nhau thì KHÔNG gọi API', () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    renderDatLai();

    fireEvent.change(screen.getByLabelText('Mật khẩu mới'), {
      target: { value: 'mat-khau-moi-123' },
    });
    fireEvent.change(screen.getByLabelText('Xác nhận mật khẩu'), {
      target: { value: 'go-nham-roi' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Đổi mật khẩu' }));

    expect(screen.getByRole('alert')).toHaveTextContent('chưa giống nhau');
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('token đã dùng rồi thì hiện đúng câu backend giải thích', async () => {
    vi.stubGlobal(
      'fetch',
      mockLoi(
        'UNAUTHORIZED',
        'Đường dẫn này đã được dùng rồi. Hãy yêu cầu gửi lại thư mới.',
        401,
      ),
    );
    renderDatLai();

    fireEvent.change(screen.getByLabelText('Mật khẩu mới'), {
      target: { value: 'mat-khau-moi-123' },
    });
    fireEvent.change(screen.getByLabelText('Xác nhận mật khẩu'), {
      target: { value: 'mat-khau-moi-123' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Đổi mật khẩu' }));

    // KHÔNG được hiện "Phiên đăng nhập đã hết hạn" (câu soạn sẵn cho mã UNAUTHORIZED).
    expect(await screen.findByRole('alert')).toHaveTextContent('đã được dùng rồi');
  });
});
