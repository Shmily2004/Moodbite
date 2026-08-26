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
import { useT } from '@/shared/i18n';
import type { Khoa } from '@/shared/i18n';

import {
  IconCold,
  IconNight,
  IconPin,
  IconSnack,
  IconSoup,
  IconSunrise,
} from '@/shared/ui';

export interface NeedPreset {
  id: string;
  /** Khoá từ điển cho tiêu đề và mô tả — hai thẻ này cũng phải dịch được. */
  nhanTitle: Khoa;
  nhanDesc: Khoa;
  /** Icon minh hoạ. Component chứ không phải emoji — xem `shared/ui/icons.tsx`. */
  Icon: (props: { className?: string }) => JSX.Element;
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
    nhanTitle: 'need.gan-day.title',
    nhanDesc: 'need.gan-day.desc',
    Icon: IconPin,
    apply: { maxDistanceKm: BAN_KINH_GAN },
  },
  {
    id: 'an-dem',
    nhanTitle: 'need.an-dem.title',
    nhanDesc: 'need.an-dem.desc',
    Icon: IconNight,
    apply: { mealTimes: ['khuya'] },
  },
  {
    id: 'bua-sang',
    nhanTitle: 'need.bua-sang.title',
    nhanDesc: 'need.bua-sang.desc',
    Icon: IconSunrise,
    apply: { mealTimes: ['sang'] },
  },
  {
    id: 'an-vat',
    nhanTitle: 'need.an-vat.title',
    nhanDesc: 'need.an-vat.desc',
    Icon: IconSnack,
    apply: { mealTimes: ['an_vat'] },
  },
  {
    id: 'mon-nuoc',
    nhanTitle: 'need.mon-nuoc.title',
    nhanDesc: 'need.mon-nuoc.desc',
    Icon: IconSoup,
    apply: { cookingMethods: ['nuoc'], temperatures: ['hot'] },
  },
  {
    id: 'do-mat',
    nhanTitle: 'need.do-mat.title',
    nhanDesc: 'need.do-mat.desc',
    Icon: IconCold,
    apply: { temperatures: ['cold'] },
  },
];

export interface ExploreNeedsProps {
  onPick: (preset: NeedPreset) => void;
}

export function ExploreNeeds({ onPick }: ExploreNeedsProps) {
  const t = useT();
  return (
    <section className="needs">
      <h2 className="section-title">
        <span aria-hidden="true">🧭</span> {t('needs.title')}
      </h2>
      <p className="section-sub">{t('needs.sub')}</p>

      <ul className="needs__grid">
        {NHU_CAU.map((preset) => (
          <li key={preset.id}>
            <button type="button" className="needcard" onClick={() => onPick(preset)}>
              <preset.Icon className="needcard__icon-svg" />
              <span className="needcard__body">
                <span className="needcard__title">{t(preset.nhanTitle)}</span>
                <span className="needcard__desc">{t(preset.nhanDesc)}</span>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
