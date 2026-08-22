/**
 * "Gợi ý nhanh theo mood" — hàng thẻ bấm một phát là lọc luôn.
 *
 * ⚠️ MỖI THẺ PHẢI ÁNH XẠ VÀO MỘT BỘ LỌC CÓ THẬT Ở BACKEND.
 * Bản thiết kế vẽ 7 thẻ: Thèm cay · Thư giãn · Lười nấu · Hẹn hò · Healthy · Trời mưa ·
 * Đồ nướng. Backend chỉ có ĐÚNG 4 mood (`happy`, `sad`, `excited`, `relaxed` — xem
 * `src/domain/value_objects/mood.py`) cộng với các bộ lọc thời tiết / cách chế biến /
 * nhiệt độ. "Lười nấu" và "Hẹn hò" KHÔNG có gì phía sau để lọc, nên không vẽ ra: một cái
 * nút bấm vào mà kết quả không đổi thì tệ hơn là không có nút.
 *
 * Muốn có đủ 7 thẻ như thiết kế thì phải THÊM MOOD Ở BACKEND trước (thêm hồ sơ điểm trong
 * `MOOD_PROFILES`), rồi thêm một dòng vào bảng dưới đây.
 */
export interface MoodChoice {
  /** Nhóm bộ lọc trong `useDishSuggestions` — quyết định bấm vào thì lọc theo cái gì. */
  group: 'mood' | 'weather' | 'cookingMethods' | 'temperatures';
  value: string;
  label: string;
  emoji: string;
}

/** Bảng ánh xạ. Mỗi dòng đều đã đối chiếu với giá trị backend chấp nhận. */
export const LUA_CHON_NHANH: MoodChoice[] = [
  { group: 'mood', value: 'excited', label: 'Thèm cay', emoji: '🌶️' },
  { group: 'mood', value: 'relaxed', label: 'Thư giãn', emoji: '☕' },
  { group: 'mood', value: 'happy', label: 'Vui vẻ', emoji: '😊' },
  { group: 'mood', value: 'sad', label: 'Cần an ủi', emoji: '🍲' },
  { group: 'weather', value: 'rain', label: 'Trời mưa', emoji: '🌧️' },
  { group: 'cookingMethods', value: 'nuong', label: 'Đồ nướng', emoji: '🔥' },
  { group: 'temperatures', value: 'hot', label: 'Món nóng', emoji: '🍜' },
];

export interface MoodQuickPickProps {
  /**
   * Tiêu đề. Khách thấy "Gợi ý nhanh theo mood"; người đã đăng nhập thấy câu hỏi trực
   * tiếp "Mood của bạn hôm nay là gì?" — chốt của chủ dự án 2026-08-22, để trang chủ của
   * người đã đăng nhập có cảm giác đang nói chuyện với chính họ.
   */
  title?: string;
  /** Giá trị đang được chọn của từng nhóm, để tô đậm thẻ tương ứng. */
  dangChon: (choice: MoodChoice) => boolean;
  onPick: (choice: MoodChoice) => void;
  /** Mở bảng lọc đầy đủ — chỗ có mọi thứ mà 7 thẻ này không phủ hết. */
  onShowAll: () => void;
}

export function MoodQuickPick({
  title = 'Gợi ý nhanh theo mood',
  dangChon,
  onPick,
  onShowAll,
}: MoodQuickPickProps) {
  return (
    <section className="quickpick">
      <h2 className="section-title">{title}</h2>

      <ul className="quickpick__row">
        {LUA_CHON_NHANH.map((choice) => {
          const chon = dangChon(choice);
          return (
            <li key={`${choice.group}:${choice.value}`}>
              <button
                type="button"
                className={chon ? 'moodcard moodcard--on' : 'moodcard'}
                // `aria-pressed` chứ không phải chỉ đổi màu: người dùng trình đọc màn hình
                // cũng phải biết thẻ nào đang bật.
                aria-pressed={chon}
                onClick={() => onPick(choice)}
              >
                <span className="moodcard__emoji" aria-hidden="true">
                  {choice.emoji}
                </span>
                <span className="moodcard__label">{choice.label}</span>
              </button>
            </li>
          );
        })}

        <li>
          <button type="button" className="moodcard moodcard--more" onClick={onShowAll}>
            <span className="moodcard__emoji" aria-hidden="true">
              •••
            </span>
            <span className="moodcard__label">Xem thêm</span>
          </button>
        </li>
      </ul>
    </section>
  );
}
