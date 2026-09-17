/**
 * Phần GIỚI THIỆU MÓN ở đầu trang chi tiết món (tách khỏi `DishPage.tsx` 2026-09-16 để
 * file trang giữ dưới ~300 dòng). Component "ngu": chỉ nhận món và báo khi bấm "Chỉnh sửa".
 */
import { IconFilter } from '@/shared/ui';
import type { DishItem } from '@/shared/api';
import {
  describeCookingMethod,
  describeIntroState,
  describeMealTimes,
  describeSource,
  describeSpice,
  describeTemperature,
} from '@/entities/dish';

interface DishIntroProps {
  dish: DishItem;
  onEditFilters: () => void;
}

export function DishIntro({ dish, onEditFilters }: DishIntroProps) {
  return (
    <section className="dish-detail">
      {dish.image_url && <img className="dish-detail__image" src={dish.image_url} alt="" />}

      <div className="dish-detail__info">
        <h1 className="dish-detail__name">{dish.name}</h1>

        <ul className="dish__tags">
          {describeTemperature(dish.temperature) && (
            <li className="tag">{describeTemperature(dish.temperature)}</li>
          )}
          {describeCookingMethod(dish.cooking_method) && (
            <li className="tag">{describeCookingMethod(dish.cooking_method)}</li>
          )}
          {describeSpice(dish.spice_level) && (
            <li className="tag">{describeSpice(dish.spice_level)}</li>
          )}
          {describeMealTimes(dish.meal_times) && (
            <li className="tag tag--muted">{describeMealTimes(dish.meal_times)}</li>
          )}
          {/* NÚT "CHỈNH SỬA" cạnh hàng thuộc tính (bản thiết kế). Mở ngăn kéo bộ lọc
              ngay tại chỗ, với các thuộc tính của chính món này bật sẵn. */}
          <li>
            <button type="button" className="tag tag--nut" onClick={onEditFilters}>
              <IconFilter /> Chỉnh sửa
            </button>
          </li>
        </ul>

        {/* GIỚI THIỆU NGẮN - nội dung chính của bước 2 trong luồng.
            Chốt 2026-08-19: thay cho danh sách nguyên liệu. Một đoạn văn nói món đó là gì
            và ăn thế nào thì dễ đọc hơn, và phủ được 100% danh mục (đo được), trong khi
            danh sách nguyên liệu chỉ phủ 87%. */}
        <h2 className="dish-detail__heading">Món này là gì?</h2>
        {dish.has_description ? (
          <p className="dish-detail__intro">{dish.description}</p>
        ) : (
          /* Rỗng nghĩa là CHƯA TRA ĐƯỢC, không phải "món này không có gì để nói".
             Nói thẳng ra thay vì để một vùng trắng (CLAUDE.md mục 4 quy tắc 1). */
          <p className="muted">{describeIntroState(false)}</p>
        )}

        {/* Nguồn dữ liệu: người đọc phải biết đoạn giới thiệu này ở đâu ra. */}
        {describeSource(dish.source) && (
          <p className="dish-detail__source small muted">
            Nguồn: {describeSource(dish.source)}
            {dish.source_url && (
              <>
                {' · '}
                <a href={dish.source_url} target="_blank" rel="noreferrer">
                  xem nguồn
                </a>
              </>
            )}
          </p>
        )}
      </div>
    </section>
  );
}
