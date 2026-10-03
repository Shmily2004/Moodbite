/**
 * Phần GIỚI THIỆU MÓN ở đầu trang chi tiết món (tách khỏi `DishPage.tsx` 2026-09-16 để
 * file trang giữ dưới ~300 dòng). Component "ngu": chỉ nhận món và báo khi bấm "Chỉnh sửa".
 */
import type { ReactNode } from 'react';
import {
  IconBoil,
  IconChili,
  IconClock,
  IconCold,
  IconFlame,
  IconHotBowl,
  IconMix,
  IconPan,
  IconPencil,
  IconSoup,
  IconSteam,
  IconStirFry,
} from '@/shared/ui';
import type { DishItem } from '@/shared/api';
import { ANH_GIAO_DIEN } from '@/shared/config';
import {
  describeCookingMethod,
  describeIntroState,
  describeMealTimes,
  describeSource,
  describeSpice,
  describeTemperature,
} from '@/entities/dish';
import { useT } from '@/shared/i18n';

/**
 * Icon cho từng MÃ thuộc tính — quy tắc HIỂN THỊ thuần (2026-10-02, theo bản thiết kế:
 * chip "🔥 Đồ nướng", "🍲 Món nóng" có hình màu). Mã lạ thì không có icon, chữ vẫn hiện.
 */
const ICON_CACH_CHE_BIEN: Record<string, ReactNode> = {
  nuong: <IconFlame />,
  nuong_lo: <IconFlame />,
  nuoc: <IconSoup />,
  chien: <IconPan />,
  xao: <IconStirFry />,
  hap: <IconSteam />,
  luoc: <IconBoil />,
  tron: <IconMix />,
};
const ICON_NHIET_DO: Record<string, ReactNode> = {
  hot: <IconHotBowl />,
  cold: <IconCold />,
};

interface DishIntroProps {
  dish: DishItem;
  onEditFilters: () => void;
}

export function DishIntro({ dish, onEditFilters }: DishIntroProps) {
  const t = useT();
  const spice = describeSpice(dish.spice_level, t);
  const nhietDo = describeTemperature(dish.temperature, t);
  const cachCheBien = describeCookingMethod(dish.cooking_method, t);
  const bua = describeMealTimes(dish.meal_times, t);
  const nguon = describeSource(dish.source, t);
  const tranh = ANH_GIAO_DIEN.banner_trang_chu;
  return (
    <section className="dish-detail">
      {dish.image_url && <img className="dish-detail__image" src={dish.image_url} alt="" />}

      <div className="dish-detail__info">
        <h1 className="dish-detail__name">{dish.name}</h1>

        <ul className="dish__tags dish-attrs">
          {cachCheBien && (
            <li className="dish-attr">
              {dish.cooking_method && ICON_CACH_CHE_BIEN[dish.cooking_method]}
              {cachCheBien}
            </li>
          )}
          {nhietDo && (
            <li className="dish-attr">
              {dish.temperature && ICON_NHIET_DO[dish.temperature]}
              {nhietDo}
            </li>
          )}
          {/* Mức cay: n quả ớt + CHỮ (2026-10-02). Một quả ớt mảnh đứng một mình trong
              chip trông như chip rỗng, nên nhãn "Độ cay 1/3" nay hiện ra bằng chữ luôn;
              hình ớt là trang trí (`aria-hidden` sẵn trong icon). */}
          {spice && (
            <li className="dish-attr dish-attr--cay">
              {Array.from({ length: spice.chilies }, (_, i) => (
                <IconChili key={i} />
              ))}
              {spice.label}
            </li>
          )}
          {bua && (
            <li className="dish-attr dish-attr--phu">
              <IconClock />
              {bua}
            </li>
          )}
          {/* NÚT "CHỈNH SỬA" cạnh hàng thuộc tính (bản thiết kế, icon bút chì). Mở ngăn
              kéo bộ lọc ngay tại chỗ, với các thuộc tính của chính món này bật sẵn. */}
          <li>
            <button type="button" className="dish-attr dish-attr--nut" onClick={onEditFilters}>
              <IconPencil /> {t('dishPage.edit')}
            </button>
          </li>
        </ul>

        {/* GIỚI THIỆU NGẮN - nội dung chính của bước 2 trong luồng.
            Chốt 2026-08-19: thay cho danh sách nguyên liệu. Một đoạn văn nói món đó là gì
            và ăn thế nào thì dễ đọc hơn, và phủ được 100% danh mục (đo được), trong khi
            danh sách nguyên liệu chỉ phủ 87%. */}
        <h2 className="dish-detail__heading">{t('dishPage.whatIs')}</h2>
        {dish.has_description ? (
          <p className="dish-detail__intro">{dish.description}</p>
        ) : (
          /* Rỗng nghĩa là CHƯA TRA ĐƯỢC, không phải "món này không có gì để nói".
             Nói thẳng ra thay vì để một vùng trắng (CLAUDE.md mục 4 quy tắc 1). */
          <p className="muted">{describeIntroState(false, t)}</p>
        )}

        {/* Nguồn dữ liệu: người đọc phải biết đoạn giới thiệu này ở đâu ra. */}
        {nguon && (
          <p className="dish-detail__source small muted">
            {t('dishPage.source', { source: nguon })}
            {dish.source_url && (
              <>
                {' · '}
                <a href={dish.source_url} target="_blank" rel="noreferrer">
                  {t('dishPage.viewSource')}
                </a>
              </>
            )}
          </p>
        )}
      </div>

      {/* TRANH HÀ NỘI bên phải như bản thiết kế — thuần trang trí (`alt=""` +
          `aria-hidden`), CSS ẩn ở màn hẹp để không đẩy danh sách quán xuống. */}
      {tranh && (
        <img
          className="dish-detail__art"
          src={tranh.src}
          alt=""
          aria-hidden="true"
          width={tranh.width}
          height={tranh.height}
          loading="lazy"
        />
      )}
    </section>
  );
}
