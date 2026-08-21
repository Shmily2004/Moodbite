/**
 * VIEWMODEL của nút bật/tắt nền tối.
 *
 * ĐÂY LÀ QUY TẮC HIỂN THỊ, không phải nghiệp vụ (CLAUDE.md mục 1b): nó chỉ đổi màu,
 * không đổi dữ liệu nào cả.
 *
 * BA TRẠNG THÁI, HAI THỨ ĐƯỢC LƯU:
 *   - Chưa bấm bao giờ  -> đi theo cài đặt của MÁY, và đổi theo nếu máy đổi.
 *   - Đã tự chọn        -> giữ nguyên lựa chọn đó, kể cả khi máy đổi. Ghi vào
 *                          localStorage nên mở lại trình duyệt vẫn đúng.
 *
 * Màu thật nằm ở `app/styles.css` (`:root[data-theme='dark']`). Hook này chỉ dán
 * thuộc tính `data-theme` lên thẻ <html> — CSS lo phần còn lại.
 */
import { useCallback, useEffect, useState } from 'react';

export type ThemeName = 'light' | 'dark';

const STORAGE_KEY = 'moodbite.theme';

/** Lựa chọn người dùng đã tự bấm, hoặc `null` nếu chưa bấm lần nào. */
function readChoice(): ThemeName | null {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value === 'light' || value === 'dark' ? value : null;
  } catch {
    // Trình duyệt chặn storage (chế độ riêng tư) -> coi như chưa chọn, không nổ.
    return null;
  }
}

function writeChoice(theme: ThemeName): void {
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    /* không lưu được thì lựa chọn chỉ sống trong tab này - vẫn dùng được */
  }
}

/**
 * `matchMedia` có thể KHÔNG tồn tại (jsdom lúc chạy test, trình duyệt rất cũ).
 * Thiếu thì mặc định nền sáng — đừng để test đỏ vì một API của trình duyệt.
 */
function systemTheme(): ThemeName {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return 'light';
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export interface UseThemeResult {
  theme: ThemeName;
  toggle: () => void;
}

export function useTheme(): UseThemeResult {
  const [theme, setTheme] = useState<ThemeName>(() => readChoice() ?? systemTheme());

  // Dán lên <html> chứ không phải <body>: biến CSS khai ở `:root`, mà `:root` chính là
  // thẻ <html>.
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  // Chỉ nghe máy khi người dùng CHƯA tự chọn. Đã tự chọn mà vẫn nghe thì lựa chọn của
  // họ sẽ bị hệ điều hành ghi đè lúc trời tối — đúng thứ gây khó chịu nhất.
  useEffect(() => {
    if (readChoice() !== null) return;
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return;

    const query = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = (event: MediaQueryListEvent) => {
      setTheme(event.matches ? 'dark' : 'light');
    };
    query.addEventListener('change', onChange);
    return () => query.removeEventListener('change', onChange);
  }, []);

  const toggle = useCallback(() => {
    setTheme((current) => {
      const next: ThemeName = current === 'dark' ? 'light' : 'dark';
      writeChoice(next);
      return next;
    });
  }, []);

  return { theme, toggle };
}
