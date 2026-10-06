// Tách từ DishFilters.tsx ngày 2026-10-06 vì file vượt ~300 dòng (CLAUDE.md mục 6).
// Hai khối dựng hình dùng riêng trong `DishFilters`: một hàng lọc có tiêu đề + một chip.
import type { ReactNode } from 'react';

export function FilterRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="filters__row">
      <span className="filters__label">{label}</span>
      <div className="chips">{children}</div>
    </div>
  );
}

export function Chip({
  label,
  icon,
  active,
  onClick,
}: {
  label: string;
  icon?: ReactNode;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={active ? 'chip chip--active' : 'chip'}
      aria-pressed={active}
      onClick={onClick}
    >
      {/* Icon là hình TRANG TRÍ cạnh nhãn có sẵn -> `aria-hidden` nằm sẵn trong
          component icon, trình đọc màn hình chỉ đọc nhãn. */}
      {icon}
      {label}
    </button>
  );
}
