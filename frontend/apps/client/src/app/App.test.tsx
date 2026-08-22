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
    // Không gọi API thật trong test. Trả về lỗi mạng để đi vào nhánh xấu nhất:
    // kể cả khi backend CHẾT, giao diện vẫn phải hiện ra chứ không được trắng trơn.
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('backend tat')));
    errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    errorSpy.mockRestore();
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
    // `getAllBy…`: "Bữa sáng" nay xuất hiện ở CẢ hàng "Khám phá theo nhu cầu" lẫn bảng
    // "Lọc chi tiết" — cùng một bộ lọc, hai lối vào, đúng như thiết kế.
    expect(screen.getAllByRole('button', { name: /Bữa sáng/i }).length).toBeGreaterThan(0);
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

  it('luong tim kiem vao duoc o /search', () => {
    // Giữ luồng cũ là quyết định có chủ đích (CLAUDE.md mục 8: không xoá code đang
    // chạy được). Test này khoá lại để không ai lỡ tay gỡ mất.
    renderAt('/search');

    expect(screen.getByRole('textbox')).toBeInTheDocument();
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

    const back = screen.getByRole('link', { name: /Quay lại trang tìm quán/i });
    expect(back).toHaveAttribute('href', '/');
  });
});
