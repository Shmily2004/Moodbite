// Tách từ DishFilters.tsx ngày 2026-10-06 vì file vượt ~300 dòng (CLAUDE.md mục 6).
// Chỉ chứa MÃ + ICON của từng chip; NHÃN vẫn nằm ở từ điển `filterOpt.*` (xem `khoaNhan`).
import { ICON_MOOD } from '@/shared/config';
import {
  IconBoil,
  IconCold,
  IconFrown,
  IconHotBowl,
  IconMix,
  IconMoon,
  IconNight,
  IconPan,
  IconSmile,
  IconSnack,
  IconSoup,
  IconSteam,
  IconStirFry,
  IconSun,
  IconSunrise,
} from '@/shared/ui';

/**
 * Ảnh chủ dự án gửi, dùng cho đúng những khái niệm đã có file.
 * Trả `null` khi chưa có -> nơi gọi tự lui về icon SVG.
 */
function AnhMood({ khoa }: { khoa: string }) {
  const anh = ICON_MOOD[khoa];
  if (!anh) return null;
  return <img src={anh.src} alt="" width={18} height={18} className="chip__icon" />;
}

/** Thời tiết. (Nhóm này nay đứng CUỐI cột lọc, theo `design/Filler.png` — xem `DishFilters.tsx`.) */
export const WEATHER_OPTIONS = [
  { value: 'rain', icon: <AnhMood khoa="rain" /> },
  { value: 'clear', icon: <IconSun /> },
];

export const TEMPERATURE_OPTIONS = [
  { value: 'hot', icon: <IconHotBowl /> },
  { value: 'cold', icon: <IconCold /> },
];

export const COOKING_METHOD_OPTIONS = [
  { value: 'nuong', icon: <AnhMood khoa="nuong" /> },
  { value: 'nuoc', icon: <IconSoup /> },
  { value: 'chien', icon: <IconPan /> },
  { value: 'xao', icon: <IconStirFry /> },
  { value: 'hap', icon: <IconSteam /> },
  { value: 'luoc', icon: <IconBoil /> },
  { value: 'tron', icon: <IconMix /> },
];

export const MEAL_TIME_OPTIONS = [
  { value: 'sang', icon: <IconSunrise /> },
  { value: 'trua', icon: <IconSun /> },
  { value: 'toi', icon: <IconMoon /> },
  { value: 'khuya', icon: <IconNight /> },
  { value: 'an_vat', icon: <IconSnack /> },
];

export const MOOD_OPTIONS = [
  { value: 'happy', icon: <IconSmile /> },
  { value: 'sad', icon: <IconFrown /> },
  { value: 'excited', icon: <AnhMood khoa="excited" /> },
  { value: 'relaxed', icon: <AnhMood khoa="relaxed" /> },
];
