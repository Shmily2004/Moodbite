/** VIEW: nút mặt trăng/mặt trời ở góc phải thanh trên. Chỉ JSX. */
import { useTheme } from '../model/useTheme';

import { IconMoon, IconSun } from '@/shared/ui';
import { useT } from '@/shared/i18n';

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, toggle } = useTheme();
  const dangToi = theme === 'dark';
  const t = useT();
  const nhan = dangToi ? t('theme.toLight') : t('theme.toDark');

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
      {dangToi ? <IconSun /> : <IconMoon />}
    </button>
  );
}
