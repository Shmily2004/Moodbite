/**
 * Biểu tượng nằm trong VÒNG TRÒN NỀN NHẠT — kiểu các thẻ số trong bản thiết kế admin
 * (`frontend/design/*admin.png`).
 *
 * Màu chỉ để PHÂN BIỆT thẻ khi liếc qua, không mang nghĩa nghiệp vụ nào (CLAUDE.md mục
 * 1b: frontend chỉ chứa quy tắc hiển thị). Luôn `aria-hidden` — nhãn chữ của thẻ mới là
 * thứ trình đọc màn hình cần đọc.
 */
import { Icon, type TenIcon } from './Icon';

export type MauIconTron = 'xanh' | 'cam' | 'luc' | 'tim' | 'do' | 'vang' | 'xam';

export function IconTron({
  ten,
  mau,
  nho = false,
}: {
  ten: TenIcon;
  mau: MauIconTron;
  /** Bản nhỏ dùng trong ô bảng (cột "Ảnh" của bảng món). */
  nho?: boolean;
}) {
  return (
    <span
      className={`icon-tron icon-tron--${mau}${nho ? ' icon-tron--nho' : ''}`}
      aria-hidden="true"
    >
      <Icon ten={ten} />
    </span>
  );
}
