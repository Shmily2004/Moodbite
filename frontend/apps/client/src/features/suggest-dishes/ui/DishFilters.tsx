/**
 * Hàng chip lọc của trang chủ - component "NGU": chỉ nhận props và báo sự kiện lên trên.
 *
 * ĐÂY LÀ CỬA VÀO CHÍNH của sản phẩm theo mô tả của chủ dự án: "người dùng dùng bộ lọc lọc
 * ra những yêu cầu như nay trời mưa, muốn ăn đồ nướng, đồ nóng".
 *
 * Mã gửi lên backend là chuỗi KHÔNG DẤU ('nuong', 'sang'); nhãn tiếng Việt chỉ nằm ở đây.
 * Đổi nhãn không được làm đổi mã - mã là hợp đồng với backend.
 */
import type { DishFilterState, MultiSelectGroup, SingleSelectGroup } from '../model/useDishSuggestions';

/** Thứ tự CÓ CHỦ ĐÍCH: thời tiết trước vì đó là ví dụ đầu tiên người dùng nghĩ tới. */
const WEATHER_OPTIONS = [
  { value: 'rain', label: '🌧️ Trời mưa' },
  { value: 'clear', label: '☀️ Trời nắng' },
];

const TEMPERATURE_OPTIONS = [
  { value: 'hot', label: '🍜 Đồ nóng' },
  { value: 'cold', label: '🧊 Đồ mát' },
];

const COOKING_METHOD_OPTIONS = [
  { value: 'nuong', label: '🔥 Đồ nướng' },
  { value: 'nuoc', label: '🍲 Món nước' },
  { value: 'chien', label: '🍤 Chiên rán' },
  { value: 'xao', label: '🥘 Xào' },
  { value: 'hap', label: '☁️ Hấp' },
  { value: 'luoc', label: '💧 Luộc' },
  { value: 'tron', label: '🥗 Trộn' },
];

const MEAL_TIME_OPTIONS = [
  { value: 'sang', label: 'Bữa sáng' },
  { value: 'trua', label: 'Bữa trưa' },
  { value: 'toi', label: 'Bữa tối' },
  { value: 'khuya', label: 'Đêm khuya' },
  { value: 'an_vat', label: 'Ăn vặt' },
];

const MOOD_OPTIONS = [
  { value: 'happy', label: '😊 Vui' },
  { value: 'sad', label: '😔 Buồn' },
  { value: 'excited', label: '🌶️ Hào hứng' },
  { value: 'relaxed', label: '☕ Thư giãn' },
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
            active={filters.weather === option.value}
            onClick={() => props.onSetSingle('weather', option.value)}
          />
        ))}
        {MOOD_OPTIONS.map((option) => (
          <Chip
            key={option.value}
            label={option.label}
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
            active={filters.temperatures.includes(option.value)}
            onClick={() => props.onToggle('temperatures', option.value)}
          />
        ))}
        {COOKING_METHOD_OPTIONS.map((option) => (
          <Chip
            key={option.value}
            label={option.label}
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
  active,
  onClick,
}: {
  label: string;
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
      {label}
    </button>
  );
}
