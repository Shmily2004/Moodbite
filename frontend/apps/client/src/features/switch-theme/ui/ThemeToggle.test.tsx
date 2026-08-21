/**
 * Nút đổi nền phải thực sự ĐỔI ĐƯỢC, không chỉ hiện ra rồi thôi.
 *
 * Kiểm đúng hai thứ mà phần còn lại của app dựa vào:
 *   1. thuộc tính `data-theme` trên <html> — CSS bám vào đúng cái này để đổi màu;
 *   2. khoá localStorage `moodbite.theme` — phải KHỚP với đoạn script trong `index.html`.
 *      Hai chỗ đó buộc phải chép lại tên khoá (script chạy trước bundle nên không import
 *      được), nên test này chính là chốt chặn cho việc chúng lệch nhau.
 */
import { describe, expect, it, beforeEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { ThemeToggle } from './ThemeToggle';

describe('ThemeToggle', () => {
  beforeEach(() => {
    localStorage.clear();
    delete document.documentElement.dataset.theme;
  });

  it('mặc định là nền sáng khi máy không báo gì (jsdom không có matchMedia)', () => {
    render(<ThemeToggle />);
    expect(document.documentElement.dataset.theme).toBe('light');
  });

  it('bấm một cái là sang nền tối và ghi nhớ lựa chọn', () => {
    render(<ThemeToggle />);

    fireEvent.click(screen.getByRole('button', { name: 'Chuyển sang nền tối' }));

    expect(document.documentElement.dataset.theme).toBe('dark');
    expect(localStorage.getItem('moodbite.theme')).toBe('dark');
  });

  it('bấm lần nữa thì quay lại nền sáng', () => {
    render(<ThemeToggle />);

    fireEvent.click(screen.getByRole('button', { name: 'Chuyển sang nền tối' }));
    fireEvent.click(screen.getByRole('button', { name: 'Chuyển sang nền sáng' }));

    expect(document.documentElement.dataset.theme).toBe('light');
    expect(localStorage.getItem('moodbite.theme')).toBe('light');
  });

  it('mở lại trang thì dùng lại lựa chọn đã lưu', () => {
    localStorage.setItem('moodbite.theme', 'dark');

    render(<ThemeToggle />);

    expect(document.documentElement.dataset.theme).toBe('dark');
  });
});
