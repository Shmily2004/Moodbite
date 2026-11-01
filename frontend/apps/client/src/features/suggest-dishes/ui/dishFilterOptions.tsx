// Tách từ DishFilters.tsx ngày 2026-10-06 vì file vượt ~300 dòng (CLAUDE.md mục 6).
// Chỉ chứa MÃ + ICON của từng chip; NHÃN vẫn nằm ở từ điển `filterOpt.*` (xem `khoaNhan`).
import {
  IconBoil,
  IconChili,
  IconFlame,
  IconLeaf,
  IconRain,
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

// MỘT bộ icon nét SVG cho mọi chip (2026-10-28) - trước đó 4 chip dùng ảnh PNG màu,
// lẫn với icon nét ở các chip bên cạnh. Hình TRÙNG với hàng ô mood trang chủ.
/** Thời tiết. (Nhóm này nay đứng CUỐI cột lọc, theo `design/Filler.png` — xem `DishFilters.tsx`.) */
export const WEATHER_OPTIONS = [
  { value: 'rain', icon: <IconRain /> },
  { value: 'clear', icon: <IconSun /> },
];

export const TEMPERATURE_OPTIONS = [
  { value: 'hot', icon: <IconHotBowl /> },
  { value: 'cold', icon: <IconCold /> },
];

export const COOKING_METHOD_OPTIONS = [
  { value: 'nuong', icon: <IconFlame /> },
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
  { value: 'excited', icon: <IconChili /> },
  { value: 'relaxed', icon: <IconLeaf /> },
];
