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
import { useId, useState } from 'react';
import type { ReactNode } from 'react';
import type { DishFilterState, MultiSelectGroup, SingleSelectGroup } from '../model/useDishFilterState';
import { DistanceSlider } from './DistanceSlider';
import { ICON_MOOD } from '@/shared/config';
import {
  IconBoil,
  IconCold,
  IconFrown,
  IconInfo,
  IconHotBowl,
  IconMix,
  IconMoon,
  IconNight,
  IconPan,
  IconPin,
  IconSmile,
  IconSnack,
  IconSoup,
  IconSteam,
  IconStirFry,
  IconSun,
  IconSunrise,
} from '@/shared/ui';
import { useT } from '@/shared/i18n';

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

/** Thời tiết. (Nhóm này nay đứng CUỐI cột lọc, theo `design/Filler.png` — xem dưới.) */
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

interface DishFiltersProps {
  filters: DishFilterState;
  onToggle: (group: MultiSelectGroup, value: string) => void;
  onSetSingle: (group: SingleSelectGroup, value: string | null) => void;
  onSetMaxDistanceKm: (value: number | null) => void;
  onSetOnlyWithPrice: (value: boolean) => void;
  onReset: () => void;
  activeFilterCount: number;
  locationIsDefault: boolean;
  /**
   * Câu nói rõ ĐIỂM NÀO đang được dùng ("Địa chỉ đã lưu: Nhà"…) — lấy từ
   * `useUserLocation().label`. Bỏ trống thì suy từ `locationIsDefault` như trước.
   */
  locationLabel?: string;
  locationLoading: boolean;
  onRequestLocation: () => void;
}

export function DishFilters(props: DishFiltersProps) {
  const { filters } = props;
  const t = useT();
  // Phần giải thích của công tắc giá mặc định THU GỌN (2026-10-02): đoạn 5 dòng chữ nhỏ
  // từng chiếm nửa cột lọc. Vẫn mở được bằng nút ⓘ (bàn phím + trình đọc màn hình đọc
  // được trạng thái mở/đóng qua `aria-expanded`), và nội dung vẫn nằm sẵn trong DOM.
  const [moGiaiThichGia, setMoGiaiThichGia] = useState(false);
  const idGiaiThich = useId();

  /*
    THỨ TỰ NHÓM theo `design/Filler.png` (đổi 2026-10-02):
      món gì -> khoảng cách -> chỉ quán có giá -> bữa -> tâm trạng -> thời tiết.
    Chỉ đổi CHỖ ĐẶT, không đổi hành vi: mỗi nút vẫn gọi đúng hàm cũ với đúng mã cũ.
    Thời tiết và tâm trạng trước đây chung một hàng "Hôm nay thế nào?"; bản thiết kế tách
    làm hai nhóm có tiêu đề riêng, dễ dò hơn khi cột hẹp.
  */
  return (
    <div className="filters">
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

      {/* KHOẢNG CÁCH: điểm đang dùng + nút đổi vị trí ở trên, thanh trượt ở dưới — như
          bản thiết kế ("Hoàn Kiếm, Hà Nội · Đổi vị trí"). */}
      <div className="filters__row filters__row--distance">
        <span className="filters__label">{t('filters.group.distance')}</span>
        <div className="filters__vi-tri">
          <IconPin className="icon-inline" />
          <span className="filters__vi-tri-nhan">
            {props.locationLabel ??
              (props.locationIsDefault ? 'Trung tâm Hà Nội' : 'Vị trí của bạn')}
          </span>
          <button
            type="button"
            className="linkish filters__doi-vi-tri"
            onClick={props.onRequestLocation}
            disabled={props.locationLoading}
          >
            {props.locationLoading ? 'Đang định vị…' : 'Vị trí của tôi'}
          </button>
        </div>
        <DistanceSlider value={filters.maxDistanceKm} onChange={props.onSetMaxDistanceKm} />
      </div>

      {/* CÔNG TẮC GIÁ đứng RIÊNG một khối, không trộn vào hàng chip.
          Lý do: nó không cùng hạng với "Đồ nướng" hay "Bữa tối". Backend đo được chỉ
          1,3% quán trong dữ liệu có giá đọc được, nên bật lên là cắt phần lớn kết quả —
          một chip nhỏ nằm lẫn giữa 20 chip khác sẽ khiến người dùng bật nhầm rồi tưởng
          khu mình ở không có gì ăn. Câu chú thích nói thẳng cái giá phải trả, và cảnh báo
          CHÍNH XÁC (bao nhiêu món/quán bị ẩn) do backend trả về trong `warnings`.
          Vẽ thành CÔNG TẮC (role="switch") như bản thiết kế, nhưng bên dưới vẫn là một
          checkbox thật -> bàn phím (Space) và trình đọc màn hình dùng y như cũ. */}
      <div className="filters__row filters__row--price">
        <div className="switch-row">
          <label className="switch">
            <input
              type="checkbox"
              role="switch"
              className="switch__input"
              checked={filters.onlyWithPrice}
              aria-describedby={idGiaiThich}
              onChange={(e) => props.onSetOnlyWithPrice(e.target.checked)}
            />
            <span className="switch__track" aria-hidden="true">
              <span className="switch__thumb" />
            </span>
            <span className="switch__label">Chỉ hiện quán có ghi giá</span>
          </label>
          <button
            type="button"
            className="switch__info"
            aria-expanded={moGiaiThichGia}
            aria-controls={idGiaiThich}
            aria-label={t('filters.price.why')}
            title={t('filters.price.why')}
            onClick={() => setMoGiaiThichGia((mo) => !mo)}
          >
            <IconInfo />
          </button>
        </div>
        {/* `hidden` chứ không gỡ khỏi DOM: `aria-describedby` của công tắc vẫn trỏ được
            tới đây, nên trình đọc màn hình đọc lời giải thích ngay cả khi đang thu gọn. */}
        <p id={idGiaiThich} className="switch__note muted small" hidden={!moGiaiThichGia}>
          Phần lớn quán trong dữ liệu chưa có giá (nguồn OpenStreetMap và Overture không
          có trường này), nên bật lên sẽ còn ít kết quả hơn nhiều. Không có giá nghĩa là
          <strong> chưa biết</strong>, không phải quán không niêm yết.
        </p>
      </div>

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

      <FilterRow label={t('filters.group.mood')}>
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

      <FilterRow label={t('filters.group.weather')}>
        {WEATHER_OPTIONS.map((option) => (
          <Chip
            key={option.value}
            label={option.label}
            icon={option.icon}
            active={filters.weather === option.value}
            onClick={() => props.onSetSingle('weather', option.value)}
          />
        ))}
      </FilterRow>

      {/* Chỉ hiện khi có gì để xoá - nút chết luôn hiện chỉ làm rối hàng lọc. */}
      {props.activeFilterCount > 0 && (
        <div className="filters__foot">
          <button className="btn btn--link" onClick={props.onReset}>
            Xoá {props.activeFilterCount} bộ lọc
          </button>
        </div>
      )}
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
