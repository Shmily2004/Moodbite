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
import { ICON_MOOD } from '@/shared/config';
import { useT } from '@/shared/i18n';
import type { Khoa } from '@/shared/i18n';

import {
  IconCold,
  IconHotBowl,
  IconMore,
  IconPan,
  IconSmile,
  IconSoup,
} from '@/shared/ui';

export interface MoodChoice {
  /** Nhóm bộ lọc trong `useDishSuggestions` — quyết định bấm vào thì lọc theo cái gì. */
  group: 'mood' | 'weather' | 'cookingMethods' | 'temperatures';
  value: string;
  /** Khoá từ điển, KHÔNG phải chữ viết sẵn — nếu không thì hàng thẻ này không dịch được. */
  nhan: Khoa;
  /**
   * Icon DỰ PHÒNG khi chủ dự án chưa gửi ảnh riêng cho lựa chọn này.
   * Component chứ không phải emoji (đổi 2026-08-25) — emoji không đảo màu theo thẻ
   * đang chọn và mỗi hệ điều hành vẽ một kiểu.
   */
  Icon: (props: { className?: string }) => JSX.Element;
}

/** Bảng ánh xạ. Mỗi dòng đều đã đối chiếu với giá trị backend chấp nhận. */
export const LUA_CHON_NHANH: MoodChoice[] = [
  { group: 'mood', value: 'excited', nhan: 'mood.card.excited', Icon: IconHotBowl },
  { group: 'mood', value: 'relaxed', nhan: 'mood.card.relaxed', Icon: IconSmile },
  { group: 'mood', value: 'happy', nhan: 'mood.card.happy', Icon: IconSmile },
  { group: 'mood', value: 'sad', nhan: 'mood.card.sad', Icon: IconSoup },
  { group: 'weather', value: 'rain', nhan: 'mood.card.rain', Icon: IconCold },
  { group: 'cookingMethods', value: 'nuong', nhan: 'mood.card.nuong', Icon: IconPan },
  { group: 'temperatures', value: 'hot', nhan: 'mood.card.hot', Icon: IconHotBowl },
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

export function MoodQuickPick({ title, dangChon, onPick, onShowAll }: MoodQuickPickProps) {
  const t = useT();
  return (
    <section className="quickpick">
      <h2 className="section-title">{title ?? t('mood.titleGuest')}</h2>

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
                {/* Có icon riêng thì dùng, chưa có thì emoji. Chủ dự án gửi bộ icon
                    dần từng cái — xem `ICON_MOOD` ở `shared/config/images.ts`. */}
                {ICON_MOOD[choice.value] ? (
                  <img
                    className="moodcard__icon"
                    src={ICON_MOOD[choice.value]!.src}
                    alt=""
                    width={ICON_MOOD[choice.value]!.width}
                    height={ICON_MOOD[choice.value]!.height}
                    aria-hidden="true"
                  />
                ) : (
                  <choice.Icon className="moodcard__icon-svg" />
                )}
                <span className="moodcard__label">{t(choice.nhan)}</span>
              </button>
            </li>
          );
        })}

        <li>
          <button type="button" className="moodcard moodcard--more" onClick={onShowAll}>
            <IconMore className="moodcard__icon-svg" />
            <span className="moodcard__label">{t('mood.more')}</span>
          </button>
        </li>
      </ul>
    </section>
  );
}
