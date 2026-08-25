/**
 * Thẻ MÓN ĂN - component "NGU": chỉ nhận props và render.
 *
 * KHÔNG gọi API, KHÔNG giữ state, KHÔNG chứa quy tắc nghiệp vụ.
 *
 * Dựng theo `design/Home.jpg` (2026-08-22): ảnh to phía trên, trái tim ở góc ảnh, nhãn
 * "MoodBite đề xuất" cho món xếp đầu, rồi tên và một dòng thông tin.
 *
 * ⚠️ ⭐ 4.7 TRONG BẢN THIẾT KẾ VẪN KHÔNG CÓ DỮ LIỆU, CỐ TÌNH BỎ TRỐNG.
 *   MÓN không có trường rating. Chỉ QUÁN mới có, và chỉ **2,7%** quán có (1.145/43.119).
 *   Muốn hiện thì backend phải tính trung bình rating các quán bán món đó — và trung bình
 *   của 2,7% mẫu thì tự nó cũng là một con số đáng ngờ. Bịa ra là kiểu sai nghiêm trọng
 *   nhất của dự án (CLAUDE.md mục 4).
 *
 * ⚠️ 📍 KHOẢNG CÁCH ĐÃ BỎ KHỎI THẺ MÓN (2026-08-25, chủ dự án chốt).
 *   Con số là THẬT (`nearest_restaurant_km` = quán gần nhất bán món này), nhưng đặt trên
 *   THẺ MÓN thì nó nói dối về mặt ý nghĩa: MÓN không có vị trí, chỉ QUÁN mới có. Người
 *   nhìn thấy "Bún chả · 1,2 km" sẽ hiểu là "món này cách 1,2 km", một câu vô nghĩa.
 *   Khoảng cách thuộc về danh sách QUÁN ở trang chi tiết món — đúng chỗ nó trả lời được
 *   câu "đi bao xa thì ăn được".
 *
 * THỨ TỰ THÔNG TIN (bước 1 của luồng: người dùng đang CHỌN MÓN, chưa quan tâm quán):
 *   1. ảnh + tên món
 *   2. SỐ QUÁN GẦN BẠN  <- trả lời ngay "bấm vào có dẫn tới đâu không"
 *   3. VÌ SAO món này được gợi ý
 */
import type { DishItem } from '@/shared/api';
import { describeRestaurantCount } from '../model/format';

interface DishCardProps {
  dish: DishItem;
  onOpen?: (dish: DishItem) => void;
  /** Đã lưu chưa. Không truyền `onToggleSave` thì trái tim không hiện. */
  saved?: boolean;
  onToggleSave?: (dish: DishItem) => void;
}

export function DishCard({ dish, onOpen, saved = false, onToggleSave }: DishCardProps) {
  const unavailable = dish.restaurant_count <= 0;
  // `rank_position` 1 = món backend xếp đầu. Nhãn nói đúng nguồn gốc của nó.
  const deXuat = dish.rank_position === 1;

  return (
    <li className="dishcard-wrap">
      <article
        className={unavailable ? 'dishcard dishcard--empty' : 'dishcard'}
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
        <div className="dishcard__media">
          <DishThumb name={dish.name} imageUrl={dish.image_url} />

          {deXuat && <span className="dishcard__badge">MoodBite đề xuất</span>}

          {onToggleSave && (
            <button
              type="button"
              className={saved ? 'dishcard__heart dishcard__heart--on' : 'dishcard__heart'}
              aria-label={saved ? `Bỏ lưu ${dish.name}` : `Lưu ${dish.name}`}
              aria-pressed={saved}
              // Chặn nổi bọt: bấm tim KHÔNG được mở luôn trang chi tiết món.
              onClick={(event) => {
                event.stopPropagation();
                onToggleSave(dish);
              }}
            >
              <span aria-hidden="true">{saved ? '♥' : '♡'}</span>
            </button>
          )}
        </div>

        <div className="dishcard__body">
          <h3 className="dishcard__name">{dish.name}</h3>

          {/* Số quán đứng NGAY dưới tên: nó quyết định người dùng có bấm hay không. */}
          <p
            className={
              unavailable ? 'dishcard__meta dishcard__meta--empty' : 'dishcard__meta'
            }
          >
            {describeRestaurantCount(dish.restaurant_count)}
          </p>

          {dish.reasons.length > 0 && (
            <p className="dishcard__why">{dish.reasons.join(' · ')}</p>
          )}
        </div>
      </article>
    </li>
  );
}

/**
 * Ảnh món. Chưa có ảnh là chuyện BÌNH THƯỜNG (ảnh lấy từ Wikipedia, không phải món nào
 * cũng có bài — đo được 140/747 món chưa có) - hiện chữ cái đầu thay vì khung vỡ.
 */
function DishThumb({ name, imageUrl }: { name: string; imageUrl?: string | null }) {
  if (!imageUrl) {
    return (
      <div className="dishcard__thumb dishcard__thumb--empty" aria-hidden="true">
        {name.slice(0, 1)}
      </div>
    );
  }
  return (
    <img
      className="dishcard__thumb"
      src={imageUrl}
      alt=""
      loading="lazy"
      // Link ảnh ngoài có thể chết. Hỏng thì ẩn đi, để lộ nền ô bên dưới thay vì hiện
      // biểu tượng ảnh vỡ của trình duyệt.
      onError={(event) => {
        event.currentTarget.style.display = 'none';
      }}
    />
  );
}
