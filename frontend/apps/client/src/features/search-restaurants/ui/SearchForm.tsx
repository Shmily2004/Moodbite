/**
 * Ô tìm kiếm — component "NGU": chỉ nhận props và báo sự kiện lên trên.
 *
 * Đề án mục 2: người dùng GÕ NHU CẦU BẰNG CÂU TỰ NHIÊN thay vì bị ép chọn bộ lọc cứng.
 * Nút mood chỉ là lối tắt, không phải cách dùng chính.
 *
 * TÁCH LÀM HAI vì bố cục mới đặt chúng ở hai chỗ khác nhau:
 *   - `SearchForm`         → ô nhập, nằm trên THANH TRÊN
 *   - `SearchForm.Filters` → hàng chip lọc, nằm ngay dưới thanh trên
 * Cùng một feature nên để cùng file; tách file chỉ làm khó tìm.
 */
import { useState } from 'react';
import {
  IconClock,
  IconFilter,
  IconFrown,
  IconHotBowl,
  IconPin,
  IconSmile,
} from '@/shared/ui';
import { useNgonNgu, useT } from '@/shared/i18n';
import type { Khoa } from '@/shared/i18n';
import type { FormEvent } from 'react';

/**
 * Câu mẫu CỐ Ý GIỮ TIẾNG VIỆT ở cả bản tiếng Anh: dữ liệu quán và phép so khớp chỉ có
 * tiếng Việt, nên câu mẫu tiếng Anh sẽ trả về rỗng. Bản tiếng Anh thêm lời dẫn
 * "Try (in Vietnamese):" để người đọc hiểu vì sao (`search.examplesLead`).
 */
const EXAMPLE_QUERIES = [
  'phở bò gần đây',
  'chỗ yên tĩnh để làm việc',
  'quán lẩu ấm cúng',
  'ăn nhẹ, tốt cho sức khoẻ',
];

const MOOD_SHORTCUTS: Array<{ value: string; nhan: Khoa; Icon: typeof IconSmile }> = [
  // Icon là COMPONENT, không phải emoji trong nhãn — xem `shared/ui/icons.tsx`.
  // Nhãn dùng CHUNG khoá `filterOpt.mood.*` với hàng chip lọc món: cùng một mood thì
  // cùng một chữ ở mọi nơi.
  { value: 'happy', nhan: 'filterOpt.mood.happy', Icon: IconSmile },
  { value: 'sad', nhan: 'filterOpt.mood.sad', Icon: IconFrown },
  { value: 'excited', nhan: 'filterOpt.mood.excited', Icon: IconHotBowl },
  { value: 'relaxed', nhan: 'filterOpt.mood.relaxed', Icon: IconSmile },
];

const RADIUS_OPTIONS = [2, 5, 10, 20];

interface SearchFormProps {
  queryText: string;
  onQueryTextChange: (value: string) => void;
  loading: boolean;
  onSubmit: () => void;
}

export function SearchForm({
  queryText,
  onQueryTextChange,
  loading,
  onSubmit,
}: SearchFormProps) {
  const t = useT();
  const submit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit();
  };

  return (
    <form className="search__form" onSubmit={submit} role="search">
      <input
        className="search__input"
        type="text"
        value={queryText}
        onChange={(event) => onQueryTextChange(event.target.value)}
        placeholder={t('search.placeholder')}
        aria-label={t('search.inputLabel')}
      />
      <button className="btn btn--primary" type="submit" disabled={loading}>
        {loading ? '…' : t('search.submit')}
      </button>
    </form>
  );
}

interface FiltersProps {
  maxDistanceKm: number | null;
  onMaxDistanceChange: (value: number | null) => void;
  openNow: boolean;
  onOpenNowChange: (value: boolean) => void;
  locationIsDefault: boolean;
  /** Điểm nào đang được dùng — xem `DishFilters.locationLabel`. */
  locationLabel?: string;
  locationLoading: boolean;
  onRequestLocation: () => void;
  onPickMood: (mood: string) => void;
  onPickExample: (query: string) => void;
  /** Chỉ gợi ý câu mẫu khi ô tìm còn trống - gõ rồi thì gợi ý thành nhiễu. */
  showExamples: boolean;
}

function Filters(props: FiltersProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const { ngonNgu, t } = useNgonNgu();

  return (
    <>
      <div className="chips">
        <button
          className={props.openNow ? 'chip chip--active' : 'chip'}
          onClick={() => props.onOpenNowChange(!props.openNow)}
          aria-pressed={props.openNow}
        >
          <IconClock /> {t('search.openNow')}
        </button>
        {MOOD_SHORTCUTS.map((mood) => (
          <button
            key={mood.value}
            className="chip"
            onClick={() => props.onPickMood(mood.value)}
          >
            <mood.Icon /> {t(mood.nhan)}
          </button>
        ))}
        <button
          className={showAdvanced ? 'chip chip--active' : 'chip'}
          onClick={() => setShowAdvanced((open) => !open)}
          aria-expanded={showAdvanced}
        >
          <IconFilter /> {t('search.filters')}
        </button>

        {props.showExamples && ngonNgu !== 'vi' && (
          <span className="chips__lead muted small">{t('search.examplesLead')}</span>
        )}
        {props.showExamples &&
          EXAMPLE_QUERIES.map((query) => (
            // `lang="vi"`: trình đọc màn hình đọc câu mẫu bằng giọng Việt dù trang đang Anh.
            <button
              key={query}
              className="chip"
              lang="vi"
              onClick={() => props.onPickExample(query)}
            >
              {query}
            </button>
          ))}
      </div>

      {showAdvanced && (
        <div className="search__controls">
          <label>
            {t('search.radius')}{' '}
            <select
              value={props.maxDistanceKm ?? ''}
              onChange={(event) =>
                props.onMaxDistanceChange(
                  event.target.value ? Number(event.target.value) : null,
                )
              }
            >
              {RADIUS_OPTIONS.map((km) => (
                <option key={km} value={km}>
                  {km} km
                </option>
              ))}
              <option value="">{t('filters.unlimited')}</option>
            </select>
          </label>

          <button
            className="btn"
            onClick={props.onRequestLocation}
            disabled={props.locationLoading}
          >
            {props.locationLoading ? t('loc.locating') : <><IconPin /> {t('loc.mine')}</>}
          </button>

          <span className="muted small">
            {props.locationLabel ??
              (props.locationIsDefault ? t('loc.center') : t('loc.yours'))}
          </span>
        </div>
      )}
    </>
  );
}

SearchForm.Filters = Filters;
