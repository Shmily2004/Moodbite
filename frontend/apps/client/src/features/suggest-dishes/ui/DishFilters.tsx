/**
 * Hàng chip lọc của trang chủ - component "NGU": chỉ nhận props và báo sự kiện lên trên.
 *
 * ĐÂY LÀ CỬA VÀO CHÍNH của sản phẩm theo mô tả của chủ dự án: "người dùng dùng bộ lọc lọc
 * ra những yêu cầu như nay trời mưa, muốn ăn đồ nướng, đồ nóng".
 *
 * Mã gửi lên backend là chuỗi KHÔNG DẤU ('nuong', 'sang'); nhãn tiếng Việt chỉ nằm ở đây.
 * Đổi nhãn không được làm đổi mã - mã là hợp đồng với backend.
 *
 * ICON, KHÔNG EMOJI (đổi 2026-08-24 theo yêu cầu chủ dự án). Lý do đã ghi sẵn ở đầu
 * `shared/ui/icons.tsx`: emoji mỗi hệ điều hành vẽ một kiểu và không đổi màu theo giao
 * diện được — chip lọc lúc bật thì đảo màu chữ, emoji đứng im trông như lỗi.
 * Thứ tự ưu tiên khi chọn hình:
 *   1. ẢNH CHỦ DỰ ÁN GỬI (`ICON_MOOD` trong `shared/config/images.ts`) — cay, thư giãn,
 *      trời mưa, đồ nướng. Đây là nhận diện riêng của sản phẩm, không vẽ lại.
 *   2. SVG trong `shared/ui/icons.tsx` cho phần còn lại.
 */
import type { ReactNode } from 'react';
import type { DishFilterState, MultiSelectGroup, SingleSelectGroup } from '../model/useDishSuggestions';
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

/**
 * ⚠️ KHÔNG THÊM HÀNG "GỢI Ý NHANH" VÀO ĐÂY. Đã thử và gỡ ngày 2026-08-24.
 *
 * Trang chủ ĐÃ CÓ HAI chỗ làm đúng việc đó, và cả hai đều đọc/ghi cùng một state:
 *   - `widgets/mood-quick-pick`  (`LUA_CHON_NHANH`): mưa · nướng · đồ nóng · 4 mood
 *   - `widgets/explore-needs`    (`NHU_CAU`)       : gần đây · ăn đêm · bữa sáng · ăn vặt
 *
 * Thêm hàng thứ ba ở đây chính là tái phạm lỗi của bản thiết kế mà nó định sửa: một
 * khái niệm nằm ở hai nơi, người dùng không biết bấm chỗ nào, và thanh "đang lọc theo"
 * không phân biệt được chip đến từ đâu. Muốn thêm gợi ý nhanh -> thêm vào `LUA_CHON_NHANH`.
 */

/** Thứ tự CÓ CHỦ ĐÍCH: thời tiết trước vì đó là ví dụ đầu tiên người dùng nghĩ tới. */
const WEATHER_OPTIONS = [
  { value: 'rain', label: 'Trời mưa', icon: <AnhMood khoa="rain" /> },
  { value: 'clear', label: 'Trời nắng', icon: <IconSun /> },
];

const TEMPERATURE_OPTIONS = [
  { value: 'hot', label: 'Đồ nóng', icon: <IconHotBowl /> },
  { value: 'cold', label: 'Đồ mát', icon: <IconCold /> },
];

const COOKING_METHOD_OPTIONS = [
  { value: 'nuong', label: 'Đồ nướng', icon: <AnhMood khoa="nuong" /> },
  { value: 'nuoc', label: 'Món nước', icon: <IconSoup /> },
  { value: 'chien', label: 'Chiên rán', icon: <IconPan /> },
  { value: 'xao', label: 'Xào', icon: <IconStirFry /> },
  { value: 'hap', label: 'Hấp', icon: <IconSteam /> },
  { value: 'luoc', label: 'Luộc', icon: <IconBoil /> },
  { value: 'tron', label: 'Trộn', icon: <IconMix /> },
];

const MEAL_TIME_OPTIONS = [
  { value: 'sang', label: 'Bữa sáng', icon: <IconSunrise /> },
  { value: 'trua', label: 'Bữa trưa', icon: <IconSun /> },
  { value: 'toi', label: 'Bữa tối', icon: <IconMoon /> },
  { value: 'khuya', label: 'Đêm khuya', icon: <IconNight /> },
  { value: 'an_vat', label: 'Ăn vặt', icon: <IconSnack /> },
];

const MOOD_OPTIONS = [
  { value: 'happy', label: 'Vui', icon: <IconSmile /> },
  { value: 'sad', label: 'Buồn', icon: <IconFrown /> },
  { value: 'excited', label: 'Hào hứng', icon: <AnhMood khoa="excited" /> },
  { value: 'relaxed', label: 'Thư giãn', icon: <AnhMood khoa="relaxed" /> },
];

const RADIUS_OPTIONS = [2, 5, 10, 20];

interface DishFiltersProps {
  filters: DishFilterState;
  onToggle: (group: MultiSelectGroup, value: string) => void;
  onSetSingle: (group: SingleSelectGroup, value: string | null) => void;
  onSetMaxDistanceKm: (value: number | null) => void;
  onReset: () => void;
  activeFilterCount: number;
  locationIsDefault: boolean;
  locationLoading: boolean;
  onRequestLocation: () => void;
}

export function DishFilters(props: DishFiltersProps) {
  const { filters } = props;

  return (
    <div className="filters">
      <FilterRow label="Hôm nay thế nào?">
        {WEATHER_OPTIONS.map((option) => (
          <Chip
            key={option.value}
            label={option.label}
            icon={option.icon}
            active={filters.weather === option.value}
            onClick={() => props.onSetSingle('weather', option.value)}
          />
        ))}
        {MOOD_OPTIONS.map((option) => (
          <Chip
            key={option.value}
            label={option.label}
            icon={option.icon}
            active={filters.mood === option.value}
            onClick={() => props.onSetSingle('mood', option.value)}
          />
        ))}
      </FilterRow>

      <FilterRow label="Muốn ăn gì?">
        {TEMPERATURE_OPTIONS.map((option) => (
          <Chip
            key={option.value}
            label={option.label}
            icon={option.icon}
            active={filters.temperatures.includes(option.value)}
            onClick={() => props.onToggle('temperatures', option.value)}
          />
        ))}
        {COOKING_METHOD_OPTIONS.map((option) => (
          <Chip
            key={option.value}
            label={option.label}
            icon={option.icon}
            active={filters.cookingMethods.includes(option.value)}
            onClick={() => props.onToggle('cookingMethods', option.value)}
          />
        ))}
      </FilterRow>

      <FilterRow label="Bữa nào?">
        {MEAL_TIME_OPTIONS.map((option) => (
          <Chip
            key={option.value}
            label={option.label}
            icon={option.icon}
            active={filters.mealTimes.includes(option.value)}
            onClick={() => props.onToggle('mealTimes', option.value)}
          />
        ))}
      </FilterRow>

      <div className="filters__foot">
        <label className="filters__radius">
          Trong vòng{' '}
          <select
            value={filters.maxDistanceKm ?? ''}
            onChange={(event) =>
              props.onSetMaxDistanceKm(
                event.target.value ? Number(event.target.value) : null,
              )
            }
          >
            {RADIUS_OPTIONS.map((km) => (
              <option key={km} value={km}>
                {km} km
              </option>
            ))}
            <option value="">Không giới hạn</option>
          </select>
        </label>

        <button
          className="btn"
          onClick={props.onRequestLocation}
          disabled={props.locationLoading}
        >
          {props.locationLoading ? 'Đang định vị…' : '📍 Vị trí của tôi'}
        </button>
        <span className="muted small">
          {props.locationIsDefault ? 'Trung tâm Hà Nội' : 'Vị trí của bạn'}
        </span>

        {/* Chỉ hiện khi có gì để xoá - nút chết luôn hiện chỉ làm rối hàng lọc. */}
        {props.activeFilterCount > 0 && (
          <button className="btn btn--link" onClick={props.onReset}>
            Xoá {props.activeFilterCount} bộ lọc
          </button>
        )}
      </div>
    </div>
  );
}

function FilterRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="filters__row">
      <span className="filters__label">{label}</span>
      <div className="chips">{children}</div>
    </div>
  );
}

function Chip({
  label,
  icon,
  active,
  onClick,
}: {
  label: string;
  icon?: ReactNode;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={active ? 'chip chip--active' : 'chip'}
      aria-pressed={active}
      onClick={onClick}
    >
      {/* Icon là hình TRANG TRÍ cạnh nhãn có sẵn -> `aria-hidden` nằm sẵn trong
          component icon, trình đọc màn hình chỉ đọc nhãn. */}
      {icon}
      {label}
    </button>
  );
}
