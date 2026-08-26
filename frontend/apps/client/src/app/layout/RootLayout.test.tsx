/**
 * Layout gốc — cụ thể là: CHÂN TRANG XUẤT HIỆN Ở ĐÂU.
 *
 * Có file này vì đã xảy ra lỗi thật (2026-08-25): chân trang được gắn vào layout gốc mà
 * chỉ loại trừ `/search`, nên nó lọt vào trang đăng nhập/đăng ký và LÀM VỠ bố cục —
 * `.auth` đặt `min-height: 100dvh` để tranh nền trải kín màn hình, thêm một khối chữ
 * bên dưới là hỏng. Chủ dự án phát hiện, không phải test.
 */
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { RootLayout } from './RootLayout';
import { ROUTES } from '@/shared/config';

function renderTai(duongDan: string) {
  return render(
    <MemoryRouter initialEntries={[duongDan]}>
      <Routes>
        <Route element={<RootLayout />}>
          <Route path="*" element={<p>nội dung trang</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

/** Chân trang nhận ra bằng phần ghi công nguồn dữ liệu — thứ bắt buộc theo giấy phép. */
function coChanTrang() {
  return screen.queryByText(/OpenStreetMap/) !== null;
}

describe('RootLayout — chân trang', () => {
  it.each([
    ['đăng nhập', ROUTES.login],
    ['đăng ký', ROUTES.register],
    ['quên mật khẩu', ROUTES.forgotPassword],
    ['đặt lại mật khẩu', ROUTES.resetPassword],
    ['xác minh email', ROUTES.verifyEmail],
    ['bản đồ', ROUTES.search],
  ])('KHÔNG hiện chân trang ở trang %s', (_ten, duongDan) => {
    renderTai(duongDan);

    expect(coChanTrang()).toBe(false);
  });

  it.each([
    ['trang chủ', ROUTES.home],
    ['kết quả gợi ý', ROUTES.recommend],
    ['tài khoản', ROUTES.account],
  ])('CÓ chân trang ở trang %s', (_ten, duongDan) => {
    renderTai(duongDan);

    expect(coChanTrang()).toBe(true);
  });

  it('chân trang ghi công đủ ba nguồn dữ liệu', () => {
    // Không phải chuyện thẩm mỹ: ODbL, CDLA và CC BY-SA đều BẮT BUỘC ghi công.
    renderTai(ROUTES.home);

    expect(screen.getByText(/OpenStreetMap/)).toBeInTheDocument();
    expect(screen.getByText(/Overture Maps/)).toBeInTheDocument();
    expect(screen.getByText(/Wikimedia Commons/)).toBeInTheDocument();
  });
});
