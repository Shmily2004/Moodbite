/**
 * Đăng xuất phải HỎI LẠI. Bấm nhầm mà không hỏi là mất phiên đăng nhập.
 */
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { LanguageProvider } from '@/shared/i18n';
import { LogoutButton } from './LogoutButton';

function renderNut(onConfirm = vi.fn()) {
  render(
    <LanguageProvider>
      <LogoutButton onConfirm={onConfirm}>Đăng xuất</LogoutButton>
    </LanguageProvider>,
  );
  return onConfirm;
}

describe('LogoutButton', () => {
  it('bấm đăng xuất chỉ mở hộp hỏi, CHƯA đăng xuất', () => {
    const onConfirm = renderNut();

    fireEvent.click(screen.getByRole('button', { name: 'Đăng xuất' }));

    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
    expect(screen.getByText('Bạn có chắc chắn muốn đăng xuất không?')).toBeInTheDocument();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it('bấm Huỷ thì đóng hộp và KHÔNG đăng xuất', () => {
    const onConfirm = renderNut();
    fireEvent.click(screen.getByRole('button', { name: 'Đăng xuất' }));

    fireEvent.click(screen.getByRole('button', { name: 'Huỷ' }));

    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it('phím Esc là huỷ', () => {
    const onConfirm = renderNut();
    fireEvent.click(screen.getByRole('button', { name: 'Đăng xuất' }));

    fireEvent.keyDown(window, { key: 'Escape' });

    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it('xác nhận trong hộp thì đăng xuất đúng MỘT lần', () => {
    const onConfirm = renderNut();
    fireEvent.click(screen.getByRole('button', { name: 'Đăng xuất' }));

    // Nút trong hộp có cùng nhãn với nút mở hộp, nên lấy trong dialog.
    const hop = screen.getByRole('alertdialog');
    fireEvent.click(hop.querySelector('.xac-nhan__dong-y') as HTMLElement);

    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
  });
});
