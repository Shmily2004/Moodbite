/**
 * Trang XÁC MINH EMAIL — mở từ đường dẫn trong thư.
 *
 * Giả lập `fetch` ở mức thấp nhất để đi qua đúng lớp `HttpClient` thật: sai đường dẫn
 * hay sai tên trường (`token`) là test đỏ ngay — cùng lý do đã ghi ở
 * `ResetPasswordPage.test.tsx`.
 */
import { describe, expect, it, vi, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { VerifyEmailPage } from '../index';

const diToi = vi.fn();
vi.mock('react-router-dom', async () => {
  // Giữ nguyên mọi thứ khác của react-router (MemoryRouter, Link, useSearchParams);
  // chỉ thay `useNavigate` để kiểm ĐÃ CHUYỂN ĐI ĐÂU mà không cần dựng cả router thật.
  const that = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...that, useNavigate: () => diToi };
});

function mockOk(email: string) {
  return vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({
      data: {
        user_id: 'u-1',
        username: 'nguoidung',
        role: 'user',
        email,
        email_verified: true,
      },
    }),
  });
}

function mockLoi(code: string, message: string, status: number) {
  return vi.fn().mockResolvedValue({
    ok: false,
    status,
    json: async () => ({ error: { code, message } }),
  });
}

function renderTrang(duongDan = '/verify-email?token=token-trong-thu') {
  return render(
    <MemoryRouter initialEntries={[duongDan]}>
      <VerifyEmailPage />
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  diToi.mockClear();
});

describe('VerifyEmailPage', () => {
  it('tự xác minh ngay khi mở trang, không cần bấm nút nào', async () => {
    const fetchMock = mockOk('ai.do@vi.du.com');
    vi.stubGlobal('fetch', fetchMock);

    renderTrang();

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const [duongDan, tuyChon] = fetchMock.mock.calls[0];
    expect(String(duongDan)).toContain('/auth/verify-email/confirm');
    expect(JSON.parse(String(tuyChon.body))).toEqual({ token: 'token-trong-thu' });
  });

  it('báo thành công sau khi xác minh xong', async () => {
    vi.stubGlobal('fetch', mockOk('ai.do@vi.du.com'));

    renderTrang();

    expect(await screen.findByText(/Đã xác minh email/)).toBeInTheDocument();
  });

  it('chỉ gọi API MỘT lần dù effect chạy lại', async () => {
    // React StrictMode chạy effect hai lần ở môi trường phát triển. Token chỉ dùng được
    // một lần, nên gọi hai lần sẽ khiến người dùng thấy "đường dẫn đã dùng rồi" ngay ở
    // lần đầu họ bấm vào — lỗi rất dễ tưởng là bug của backend.
    const fetchMock = mockOk('ai.do@vi.du.com');
    vi.stubGlobal('fetch', fetchMock);

    const { rerender } = renderTrang();
    rerender(
      <MemoryRouter initialEntries={['/verify-email?token=token-trong-thu']}>
        <VerifyEmailPage />
      </MemoryRouter>,
    );

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('hiện nguyên văn câu lỗi của backend khi token đã dùng', async () => {
    const cau = 'Đường dẫn này không còn hiệu lực — email đã được xác minh hoặc đã đổi.';
    vi.stubGlobal('fetch', mockLoi('UNAUTHORIZED', cau, 401));

    renderTrang();

    expect(await screen.findByText(cau)).toBeInTheDocument();
  });

  it('mở trang mà thiếu token thì nói rõ, KHÔNG gọi API', async () => {
    const fetchMock = mockOk('ai.do@vi.du.com');
    vi.stubGlobal('fetch', fetchMock);

    renderTrang('/verify-email');

    expect(await screen.findByText(/thiếu mã xác minh/)).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });
  it('xác minh xong thì TỰ chuyển về trang chủ', async () => {
    // Lỗi thật 2026-08-26: bấm link trong thư xong trang chỉ hiện một dòng chữ rồi đứng
    // im, người dùng không biết đã xong hay chưa.
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.stubGlobal('fetch', mockOk('ai.do@vi.du.com'));

    renderTrang();
    await screen.findByText(/Đã xác minh email/);
    expect(screen.getByText(/Đang đưa bạn về trang chủ/)).toBeInTheDocument();

    await vi.advanceTimersByTimeAsync(3_000);

    await waitFor(() => expect(diToi).toHaveBeenCalledWith('/', { replace: true }));
    vi.useRealTimers();
  });

  it('xác minh HỎNG thì Ở LẠI để người dùng đọc được lỗi', async () => {
    // Đá về trang chủ lúc lỗi là giấu mất câu lỗi và mất luôn nút gửi lại thư.
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.stubGlobal('fetch', mockLoi('UNAUTHORIZED', 'Đường dẫn đã hết hạn.', 401));

    renderTrang();
    await screen.findByText('Đường dẫn đã hết hạn.');

    await vi.advanceTimersByTimeAsync(10_000);

    expect(diToi).not.toHaveBeenCalled();
    vi.useRealTimers();
  });
});
