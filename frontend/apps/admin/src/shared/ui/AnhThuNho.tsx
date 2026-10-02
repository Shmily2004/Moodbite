/**
 * Ảnh thu nhỏ CÓ ĐƯỜNG LUI: không có link HOẶC link chết -> hiện ô giữ chỗ trống.
 *
 * VÌ SAO CẦN: ảnh quán/món là link NGOÀI (Google, Wikimedia) và chết dần theo thời gian.
 * Trước 2026-10-02, bốn chỗ dùng `<img>` trần nên link chết hiện biểu tượng "ảnh vỡ" của
 * trình duyệt — trông như lỗi của trang quản trị. Ô giữ chỗ là ô xám TRỐNG, không phải
 * ảnh mẫu: chèn ảnh mẫu là nói dối rằng đã biết quán trông thế nào.
 *
 * Nhớ link ĐÃ HỎNG chứ không chỉ cờ true/false: cùng một dòng bảng được dùng lại cho quán
 * khác (đổi trang) thì link mới phải được thử lại, không kế thừa trạng thái hỏng cũ.
 */
import { useState, type ReactNode } from 'react';

export interface AnhThuNhoProps {
  src: string | null | undefined;
  /** Lớp CSS của ảnh — ô giữ chỗ dùng chung lớp này để giữ đúng kích thước. */
  className: string;
  /** Lớp CSS THÊM vào ô giữ chỗ (nền xám, viền đứt…). */
  classNameTrong: string;
  alt?: string;
  /** Chữ bên trong ô giữ chỗ, ví dụ "Chưa có ảnh". Mặc định để trống. */
  children?: ReactNode;
}

export function AnhThuNho({ src, className, classNameTrong, alt = '', children }: AnhThuNhoProps) {
  const [linkHong, setLinkHong] = useState<string | null>(null);

  if (!src || linkHong === src) {
    return (
      <span className={`${className} ${classNameTrong}`} aria-hidden={children ? undefined : true}>
        {children}
      </span>
    );
  }
  return (
    <img
      className={className}
      src={src}
      alt={alt}
      loading="lazy"
      onError={() => setLinkHong(src)}
    />
  );
}
