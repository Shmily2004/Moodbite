/** VIEW: nút mặt trăng/mặt trời ở góc phải thanh trên. Chỉ JSX. */
import { useTheme } from '../model/useTheme';

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, toggle } = useTheme();
  const dangToi = theme === 'dark';
  const nhan = dangToi ? 'Chuyển sang nền sáng' : 'Chuyển sang nền tối';

  return (
    <button
      type="button"
      className={['theme-toggle', className].filter(Boolean).join(' ')}
      onClick={toggle}
      // `aria-label` vì nút chỉ có biểu tượng: trình đọc màn hình không đọc được emoji
      // thành câu có nghĩa. `title` để người dùng chuột rê vào cũng hiểu.
      aria-label={nhan}
      title={nhan}
      aria-pressed={dangToi}
    >
      <span aria-hidden="true">{dangToi ? '☀️' : '🌙'}</span>
    </button>
  );
}
