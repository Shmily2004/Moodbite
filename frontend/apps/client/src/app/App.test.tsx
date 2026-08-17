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

    expect(screen.getByText('MoodBite')).toBeInTheDocument();
  });

  it('trang chu hien o tim kiem de nguoi dung go nhu cau', () => {
    renderAt('/');

    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('backend chet van render duoc phan khung', () => {
    renderAt('/');

    // Chưa tìm gì -> phải có lời mời rõ ràng, không được để panel trống trơn.
    expect(screen.getByText(/Bạn đang muốn ăn gì/i)).toBeInTheDocument();
    // Chip gợi ý sẵn có nghĩa cây component dựng tới cuối, không đứt giữa chừng.
    expect(screen.getByRole('button', { name: /phở bò gần đây/i })).toBeInTheDocument();
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
