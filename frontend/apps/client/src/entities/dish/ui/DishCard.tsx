/**
 * Thẻ MÓN ĂN - component "NGU": chỉ nhận props và render.
 *
 * KHÔNG gọi API, KHÔNG giữ state, KHÔNG chứa quy tắc nghiệp vụ.
 *
 * THỨ TỰ THÔNG TIN (bước 1 của luồng: người dùng đang CHỌN MÓN, chưa quan tâm quán):
 *   1. ảnh + tên món
 *   2. SỐ QUÁN GẦN BẠN  <- trả lời ngay "bấm vào có dẫn tới đâu không"
 *   3. thuộc tính món (nóng/nguội, cách chế biến, cay)
 *   4. VÌ SAO món này được gợi ý
 */
import type { DishItem } from '@/shared/api';
import {
  describeCookingMethod,
  describeRestaurantCount,
  describeSpice,
  describeTemperature,
} from '../model/format';

interface DishCardProps {
  dish: DishItem;
  onOpen?: (dish: DishItem) => void;
}

export function DishCard({ dish, onOpen }: DishCardProps) {
  const method = describeCookingMethod(dish.cooking_method);
  const temperature = describeTemperature(dish.temperature);
  const spice = describeSpice(dish.spice_level);
  const unavailable = dish.restaurant_count <= 0;

  return (
    <li>
      <article
        className={unavailable ? 'dish dish--empty' : 'dish'}
        onClick={() => onOpen?.(dish)}
        role={onOpen ? 'button' : undefined}
        tabIndex={onOpen ? 0 : undefined}
        onKeyDown={(event) => {
          if (onOpen && (event.key === 'Enter' || event.key === ' ')) {
            event.preventDefault();
            onOpen(dish);
          }
        }}
      >
        <DishThumb name={dish.name} imageUrl={dish.image_url} />

        <div className="dish__body">
          <h3 className="dish__name">{dish.name}</h3>

          {/* Số quán đứng NGAY dưới tên: nó quyết định người dùng có bấm hay không. */}
          <p className={unavailable ? 'dish__count dish__count--empty' : 'dish__count'}>
            {describeRestaurantCount(dish.restaurant_count)}
          </p>

          <ul className="dish__tags">
            {temperature && <li className="tag">{temperature}</li>}
            {method && <li className="tag">{method}</li>}
            {spice && <li className="tag">{spice}</li>}
            {dish.cuisine && <li className="tag tag--muted">{dish.cuisine}</li>}
          </ul>

          {dish.reasons.length > 0 && (
            <p className="dish__why">{dish.reasons.join(' · ')}</p>
          )}
        </div>
      </article>
    </li>
  );
}

/**
 * Ảnh món. Chưa có ảnh là chuyện BÌNH THƯỜNG (ảnh lấy từ Wikipedia, không phải món nào
 * cũng có bài) - hiện chữ cái đầu thay vì khung vỡ.
 */
function DishThumb({ name, imageUrl }: { name: string; imageUrl?: string | null }) {
  if (!imageUrl) {
    return (
      <div className="dish__thumb dish__thumb--empty" aria-hidden="true">
        {name.slice(0, 1)}
      </div>
    );
  }
  return <img className="dish__thumb" src={imageUrl} alt="" loading="lazy" />;
}
