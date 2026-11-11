/**
 * SMOKE TEST: app PHẢI render được, và layout/route phải đăng ký đúng.
 *
 * VÌ SAO FILE NÀY QUAN TRỌNG NHẤT TRONG CẢ BỘ TEST FRONTEND:
 * đây là bản sao của bài học đã trả giá ở backend (CLAUDE.md mục 0) — app từng KHÔNG
 * khởi động được vì `NameError` ở `main.py`, trong khi TOÀN BỘ test vẫn xanh, đơn giản
 * vì không test nào import app.
 *
 * Frontend đã lặp lại đúng lỗi đó: 21 test đầu tiên chỉ kiểm `format.ts` và
 * `RestaurantCard.tsx` — hai file lá. Không test nào render `<App />`, nên màn hình
 * trắng vẫn lọt qua CI.
 *
 * Test dựng router từ mảng `routes` thật thay vì render `<App />`: nhờ vậy vào được
 * THẲNG một đường dẫn bất kỳ để kiểm cả nhánh 404.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, useRoutes } from 'react-router-dom';
import { routes } from './routes';

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

describe('App - smoke test', () => {
  let errorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    // Từ 2026-11-10 mọi trang (trừ đăng nhập/đăng ký) YÊU CẦU đăng nhập. Test giả lập một
    // phiên đăng nhập: token trong sessionStorage + `/auth/me` trả về người dùng.
    // Mọi API khác vẫn lỗi mạng — để đi vào nhánh xấu nhất: backend CHẾT, giao diện vẫn
    // phải dựng được khung chứ không được trắng trơn.
    sessionStorage.setItem('moodbite.user.token', 'token-gia-lap');
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation((url: string) => {
        if (String(url).includes('/auth/me')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              data: { user_id: 'u1', username: 'mung', role: 'user' },
            }),
          });
        }
        return Promise.reject(new Error('backend tat'));
      }),
    );
    errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    sessionStorage.clear();
    errorSpy.mockRestore();
  });

  it('khach chua dang nhap bi chuyen sang trang dang nhap, KHONG vao duoc trang chu', async () => {
    sessionStorage.clear();
    renderAt('/');

    expect(
      await screen.findByRole('heading', { name: /Chào mừng trở lại/i }),
    ).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Trời mưa/i })).not.toBeInTheDocument();
  });

  it('render duoc, khong nem loi', () => {
    expect(() => renderAt('/')).not.toThrow();
  });

  it('hien nhan MoodBite - man hinh KHONG trang', () => {
    renderAt('/');

    // Nhãn thương hiệu nay là ẢNH logo (từ 2026-08-22), không còn là chữ trong <span>.
    // `getAllBy…` vì trang chủ có logo ở thanh trên; các trang khác có thể có thêm.
    expect(screen.getAllByAltText('MoodBite').length).toBeGreaterThan(0);
  });

  it('trang chu hien BO LOC MON - buoc 1 cua luong chon mon truoc', () => {
    renderAt('/');

    // Đúng ba ví dụ chủ dự án nêu: "nay trời mưa, muốn ăn đồ nướng, đồ nóng".
    // `getAllBy…`: từ bản thiết kế 2026-08-22, trang chủ có HAI chỗ chọn cùng một điều
    // kiện — hàng "Gợi ý nhanh theo mood" ở trên và bảng "Lọc chi tiết" ở dưới. Trùng tên
    // là CỐ Ý (cùng một bộ lọc, hai lối vào), nên test phải chấp nhận nhiều kết quả.
    expect(screen.getAllByRole('button', { name: /Trời mưa/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole('button', { name: /Đồ nướng/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole('button', { name: /Đồ nóng|Món nóng/i }).length).toBeGreaterThan(0);
  });

  it('backend chet van render duoc phan khung', () => {
    renderAt('/');

    // Bộ lọc vẫn bấm được kể cả khi API chết - khung không phụ thuộc dữ liệu.
    // Khách (chưa đăng nhập) thấy KHẨU HIỆU dạng ảnh; lời chào có tên chỉ dành cho người
    // đã đăng nhập (chốt 2026-08-22). Kiểm qua `alt` vì đó là chữ thật của tấm ảnh.
    expect(screen.getByAltText(/Ăn gì ở Hà Nội/i)).toBeInTheDocument();
    // Người đã đăng nhập: nút "Lọc" (ngăn kéo bộ lọc) nằm cạnh tiêu đề kết quả và không
    // cần API để hiện. Phần "Khám phá theo nhu cầu" chỉ dành cho khách, nên không kiểm ở đây.
    expect(screen.getByRole('button', { name: /^Lọc/ })).toBeInTheDocument();
  });

  // Quyết định 2026-11-11 (chủ dự án): quên mật khẩu GIỮ luồng gửi đường dẫn qua email,
  // không đổi sang mật khẩu tạm. Link trong thư là `/reset-password?token=…` và
  // `/verify-email?token=…` — hai trang này PHẢI mở được khi chưa đăng nhập, nếu không
  // người dùng bấm link trong thư sẽ bị đá sang đăng nhập.
  it('khach chua dang nhap van mo duoc link dat lai mat khau va xac minh email trong thu', async () => {
    sessionStorage.clear();
    renderAt('/reset-password?token=abc123');
    expect(
      await screen.findByRole('heading', { name: /Đặt mật khẩu mới/i }),
    ).toBeInTheDocument();
  });

  it('duong dan CU chuyen huong sang duong dan MOI, giu nguyen token', async () => {
    // Link `/dat-lai-mat-khau?token=…` đã nằm trong hộp thư người dùng từ trước khi đổi
    // đường dẫn. Mất chuyển hướng này là những lá thư đó chết.
    renderAt('/dat-lai-mat-khau?token=abc123');

    expect(
      await screen.findByRole('heading', { name: /Đặt mật khẩu mới/i }),
    ).toBeInTheDocument();
    // Có token -> form hiện ra chứ không báo "thiếu mã đặt lại".
    expect(screen.queryByText(/thiếu mã đặt lại/i)).not.toBeInTheDocument();
  });

  it('duong dan CU cua trang mon cung chuyen huong (giu :dishId)', async () => {
    renderAt('/mon/bun-cha');

    // Chuyển sang /dishes/bun-cha -> trang món gọi API và báo lỗi mạng (fetch bị chặn
    // trong bộ test này), nghĩa là ĐÃ vào đúng trang chứ không phải 404.
    expect(await screen.findByText(/Không có trang này/i).catch(() => null)).toBeNull();
  });

  it('luong tim kiem vao duoc o /search', async () => {
    // Giữ luồng cũ là quyết định có chủ đích (CLAUDE.md mục 8: không xoá code đang
    // chạy được). Test này khoá lại để không ai lỡ tay gỡ mất.
    renderAt('/search');

    // `findBy`: từ 2026-10-02 trang này TẢI SAU (lazy route) nên xuất hiện bất đồng bộ.
    // Chờ tới 4s: lần ĐẦU vitest phải biên dịch cả cây module của trang (đo được > 1s).
    expect(await screen.findByRole('textbox', undefined, { timeout: 4000 })).toBeInTheDocument();
    expect(screen.getByText(/Bạn đang muốn ăn gì/i)).toBeInTheDocument();
  });
});

describe('Layout dung chung', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('backend tat')));
  });
  afterEach(() => vi.unstubAllGlobals());

  it('duong dan la hien 404, KHONG phai man hinh trang', () => {
    renderAt('/duong-dan-khong-ton-tai');

    expect(screen.getByText(/Không có trang này/i)).toBeInTheDocument();
  });

  it('trang 404 co loi thoat ve trang chinh', () => {
    renderAt('/duong-dan-khong-ton-tai');

    const back = screen.getByRole('link', { name: /Về trang chủ/i });
    expect(back).toHaveAttribute('href', '/');
  });
});
