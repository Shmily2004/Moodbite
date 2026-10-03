/**
 * Ô ảnh của thẻ quán.
 *
 * ⚠️ CHỈ 21.5% quán có ảnh (1064/4938). Nghĩa là "không có ảnh" là trường hợp PHỔ BIẾN,
 * không phải lỗi. Nếu để trống thì 4/5 thẻ trông như ảnh vỡ.
 *
 * Giải pháp: sinh ô màu từ CHÍNH TÊN QUÁN — cùng một quán luôn ra cùng một màu, nên
 * nhìn ổn định và có chủ đích. Kèm biểu tượng suy từ loại hình quán để đỡ trống trải.
 *
 * Biểu tượng là icon SVG ở `shared/ui/icons.tsx` (đổi từ emoji 2026-09-29, checklist A9):
 * emoji mỗi hệ điều hành vẽ một kiểu, còn SVG `currentColor` ăn màu trắng của ô.
 *
 * KHÔNG phải business logic: đây thuần là quy tắc HIỂN THỊ. Nó không đổi thứ tự kết quả.
 */
import type { ComponentType, CSSProperties, SVGProps } from 'react';
import { useT } from '@/shared/i18n';
import {
  IconBeer,
  IconBread,
  IconBubbleTea,
  IconBurger,
  IconCake,
  IconCoffee,
  IconDining,
  IconFlame,
  IconHotBowl,
  IconLeaf,
  IconPizza,
  IconRiceBowl,
  IconSeafood,
  IconSoup,
  IconSushi,
} from '@/shared/ui';

/** Băm tên quán -> góc màu 0..359. Thuật toán djb2 rút gọn, đủ tản đều cho việc này. */
function hueFromName(name: string): number {
  let hash = 5381;
  for (let i = 0; i < name.length; i += 1) {
    hash = ((hash << 5) + hash + name.charCodeAt(i)) | 0;
  }
  return Math.abs(hash) % 360;
}

type GlyphIcon = ComponentType<SVGProps<SVGSVGElement>>;

/**
 * Biểu tượng theo loại hình quán. Không khớp gì thì dùng dao dĩa chung chung.
 * THỨ TỰ CÓ CHỦ ĐÍCH: "bánh mì" phải đứng trước "bánh", khớp dòng nào trước lấy dòng đó.
 */
const GLYPHS: Array<[RegExp, GlyphIcon]> = [
  [/phở|pho\b/i, IconSoup],
  [/bún|bun\b/i, IconHotBowl],
  [/cà phê|ca phe|coffee|cafe/i, IconCoffee],
  [/trà|tra sua|milk tea|bubble/i, IconBubbleTea],
  [/bánh mì|banh mi/i, IconBread],
  [/bánh|banh|bakery|kem|dessert/i, IconCake],
  [/lẩu|lau\b|nướng|nuong|bbq/i, IconFlame],
  [/hải sản|hai san|seafood|ốc|oc\b/i, IconSeafood],
  [/pizza|ý|italian/i, IconPizza],
  [/burger|gà rán|ga ran|fast food|ăn nhanh/i, IconBurger],
  [/sushi|nhật|nhat ban|japan/i, IconSushi],
  [/chay|vegetarian|vegan/i, IconLeaf],
  [/bia|beer|pub|bar/i, IconBeer],
  [/cơm|com\b|rice/i, IconRiceBowl],
];

function glyphFor(category: string | null | undefined, name: string): GlyphIcon {
  const haystack = `${category ?? ''} ${name}`;
  for (const [pattern, glyph] of GLYPHS) {
    if (pattern.test(haystack)) return glyph;
  }
  return IconDining;
}

export interface RestaurantThumbProps {
  name: string;
  category?: string | null;
  thumbnailUrl?: string | null;
}

export function RestaurantThumb({ name, category, thumbnailUrl }: RestaurantThumbProps) {
  const t = useT();
  if (thumbnailUrl) {
    return (
      <div className="thumb">
        <img
          src={thumbnailUrl}
          alt={t('rest.photoAlt', { name })}
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
  const Glyph = glyphFor(category, name);
  return (
    <div className="thumb thumb--generated" style={style} aria-hidden="true">
      <span className="thumb__glyph">
        <Glyph />
      </span>
    </div>
  );
}
