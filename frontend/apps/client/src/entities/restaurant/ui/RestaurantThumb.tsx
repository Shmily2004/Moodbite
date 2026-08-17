/**
 * Ô ảnh của thẻ quán.
 *
 * ⚠️ CHỈ 21.5% quán có ảnh (1064/4938). Nghĩa là "không có ảnh" là trường hợp PHỔ BIẾN,
 * không phải lỗi. Nếu để trống thì 4/5 thẻ trông như ảnh vỡ.
 *
 * Giải pháp: sinh ô màu từ CHÍNH TÊN QUÁN — cùng một quán luôn ra cùng một màu, nên
 * nhìn ổn định và có chủ đích. Kèm biểu tượng suy từ loại hình quán để đỡ trống trải.
 *
 * KHÔNG phải business logic: đây thuần là quy tắc HIỂN THỊ. Nó không đổi thứ tự kết quả.
 */
import type { CSSProperties } from 'react';

/** Băm tên quán -> góc màu 0..359. Thuật toán djb2 rút gọn, đủ tản đều cho việc này. */
function hueFromName(name: string): number {
  let hash = 5381;
  for (let i = 0; i < name.length; i += 1) {
    hash = ((hash << 5) + hash + name.charCodeAt(i)) | 0;
  }
  return Math.abs(hash) % 360;
}

/** Biểu tượng theo loại hình quán. Không khớp gì thì dùng bát đũa chung chung. */
const GLYPHS: Array<[RegExp, string]> = [
  [/phở|pho\b/i, '🍜'],
  [/bún|bun\b/i, '🍲'],
  [/cà phê|ca phe|coffee|cafe/i, '☕'],
  [/trà|tra sua|milk tea|bubble/i, '🧋'],
  [/bánh mì|banh mi/i, '🥖'],
  [/bánh|banh|bakery|kem|dessert/i, '🍰'],
  [/lẩu|lau\b|nướng|nuong|bbq/i, '🍢'],
  [/hải sản|hai san|seafood|ốc|oc\b/i, '🦐'],
  [/pizza|ý|italian/i, '🍕'],
  [/burger|gà rán|ga ran|fast food|ăn nhanh/i, '🍔'],
  [/sushi|nhật|nhat ban|japan/i, '🍣'],
  [/chay|vegetarian|vegan/i, '🥗'],
  [/bia|beer|pub|bar/i, '🍺'],
  [/cơm|com\b|rice/i, '🍚'],
];

function glyphFor(category: string | null | undefined, name: string): string {
  const haystack = `${category ?? ''} ${name}`;
  for (const [pattern, glyph] of GLYPHS) {
    if (pattern.test(haystack)) return glyph;
  }
  return '🍽️';
}

export interface RestaurantThumbProps {
  name: string;
  category?: string | null;
  thumbnailUrl?: string | null;
}

export function RestaurantThumb({ name, category, thumbnailUrl }: RestaurantThumbProps) {
  if (thumbnailUrl) {
    return (
      <div className="thumb">
        <img
          src={thumbnailUrl}
          alt={`Ảnh quán ${name}`}
          loading="lazy"
          // Link ảnh Google có thể hết hạn. Hỏng thì ẩn hẳn <img>, để lộ nền ô bên dưới
          // thay vì hiện biểu tượng ảnh vỡ của trình duyệt.
          onError={(event) => {
            event.currentTarget.style.display = 'none';
          }}
        />
      </div>
    );
  }

  const style = { '--tile-h': hueFromName(name) } as CSSProperties;
  return (
    <div className="thumb thumb--generated" style={style} aria-hidden="true">
      <span className="thumb__glyph">{glyphFor(category, name)}</span>
    </div>
  );
}
