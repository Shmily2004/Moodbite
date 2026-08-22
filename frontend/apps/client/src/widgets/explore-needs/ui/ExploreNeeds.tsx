/**
 * "🧭 Khám phá theo nhu cầu" — lối vào nhanh cho người CHƯA đăng nhập.
 *
 * Chủ dự án đề xuất 6 thẻ: Ăn dưới 50K · Ăn gần đây · Ăn một mình · Đi ăn cùng bạn ·
 * Ăn đêm · Quán đang hot. Đã đối chiếu với dữ liệu thật (2026-08-22), CHỈ 2 thẻ có thứ
 * để lọc:
 *
 *   ✅ Ăn gần đây     -> `max_distance_km` (có sẵn)
 *   ✅ Ăn đêm         -> `meal_times = khuya` (có sẵn, nhưng chỉ 8/747 món gắn nhãn này)
 *   ❌ Ăn dưới 50K    -> giá là CHUỖI ("1-100.000 ₫") và chỉ 273/4000 quán có; món thì
 *                        không có giá. Không lọc được nếu backend chưa làm.
 *   ❌ Ăn một mình / Đi ăn cùng bạn -> `portion_size` chỉ 55/747 món có, và KHÔNG được
 *                        API trả ra. Cần thêm cả dữ liệu lẫn trường trong response.
 *   ❌ Quán đang hot  -> không có số liệu lượt xem/đặt nào để nói "đang hot".
 *
 * Bốn thẻ còn thiếu được thay bằng bốn nhu cầu KHÁC nhưng CÓ THẬT (bữa sáng, ăn vặt, món
 * nước, đồ mát) để hàng thẻ vẫn đủ 6 mà không có cái nào bấm vào cũng ra kết quả sai.
 * Làm được phần backend thì đổi lại bảng này là xong.
 */
export interface NeedPreset {
  id: string;
  title: string;
  desc: string;
  emoji: string;
  /** Bộ lọc sẽ được áp khi bấm. `null` nghĩa là xoá lọc của nhóm đó. */
  apply: {
    mealTimes?: string[];
    temperatures?: string[];
    cookingMethods?: string[];
    maxDistanceKm?: number | null;
  };
}

/** 2 km: đi bộ hoặc xe máy vài phút — đúng nghĩa "gần đây" ở nội thành Hà Nội. */
const BAN_KINH_GAN = 2;

export const NHU_CAU: NeedPreset[] = [
  {
    id: 'gan-day',
    title: 'Ăn gần đây',
    desc: `Món có quán trong bán kính ${BAN_KINH_GAN} km`,
    emoji: '📍',
    apply: { maxDistanceKm: BAN_KINH_GAN },
  },
  {
    id: 'an-dem',
    title: 'Ăn đêm',
    desc: 'Món hợp lúc đêm khuya',
    emoji: '🌙',
    apply: { mealTimes: ['khuya'] },
  },
  {
    id: 'bua-sang',
    title: 'Bữa sáng',
    desc: 'Bắt đầu ngày mới nhẹ nhàng',
    emoji: '🌅',
    apply: { mealTimes: ['sang'] },
  },
  {
    id: 'an-vat',
    title: 'Ăn vặt',
    desc: 'Món nhâm nhi giữa buổi',
    emoji: '🍢',
    apply: { mealTimes: ['an_vat'] },
  },
  {
    id: 'mon-nuoc',
    title: 'Món nước',
    desc: 'Phở, bún, miến… nóng hổi',
    emoji: '🍜',
    apply: { cookingMethods: ['nuoc'], temperatures: ['hot'] },
  },
  {
    id: 'do-mat',
    title: 'Đồ mát',
    desc: 'Ngày oi bức thì chọn nhóm này',
    emoji: '🧊',
    apply: { temperatures: ['cold'] },
  },
];

export interface ExploreNeedsProps {
  onPick: (preset: NeedPreset) => void;
}

export function ExploreNeeds({ onPick }: ExploreNeedsProps) {
  return (
    <section className="needs">
      <h2 className="section-title">
        <span aria-hidden="true">🧭</span> Khám phá theo nhu cầu
      </h2>
      <p className="section-sub">Không cần tài khoản — bấm một cái là xem được ngay.</p>

      <ul className="needs__grid">
        {NHU_CAU.map((preset) => (
          <li key={preset.id}>
            <button type="button" className="needcard" onClick={() => onPick(preset)}>
              <span className="needcard__emoji" aria-hidden="true">
                {preset.emoji}
              </span>
              <span className="needcard__body">
                <span className="needcard__title">{preset.title}</span>
                <span className="needcard__desc">{preset.desc}</span>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
