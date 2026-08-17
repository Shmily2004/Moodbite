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
import type { FormEvent } from 'react';

const EXAMPLE_QUERIES = [
  'phở bò gần đây',
  'chỗ yên tĩnh để làm việc',
  'quán lẩu ấm cúng',
  'ăn nhẹ, tốt cho sức khoẻ',
];

const MOOD_SHORTCUTS = [
  { value: 'happy', label: '😊 Vui' },
  { value: 'sad', label: '😔 Buồn' },
  { value: 'excited', label: '🌶️ Hào hứng' },
  { value: 'relaxed', label: '☕ Thư giãn' },
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
        placeholder="Bạn muốn ăn gì? VD: quán lẩu ấm cúng gần đây"
        aria-label="Nhu cầu của bạn"
      />
      <button className="btn btn--primary" type="submit" disabled={loading}>
        {loading ? '…' : 'Tìm'}
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
  locationLoading: boolean;
  onRequestLocation: () => void;
  onPickMood: (mood: string) => void;
  onPickExample: (query: string) => void;
  /** Chỉ gợi ý câu mẫu khi ô tìm còn trống - gõ rồi thì gợi ý thành nhiễu. */
  showExamples: boolean;
}

function Filters(props: FiltersProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  return (
    <>
      <div className="chips">
        <button
          className={props.openNow ? 'chip chip--active' : 'chip'}
          onClick={() => props.onOpenNowChange(!props.openNow)}
          aria-pressed={props.openNow}
        >
          🕒 Đang mở
        </button>
        {MOOD_SHORTCUTS.map((mood) => (
          <button
            key={mood.value}
            className="chip"
            onClick={() => props.onPickMood(mood.value)}
          >
            {mood.label}
          </button>
        ))}
        <button
          className={showAdvanced ? 'chip chip--active' : 'chip'}
          onClick={() => setShowAdvanced((open) => !open)}
          aria-expanded={showAdvanced}
        >
          ⚙️ Bộ lọc
        </button>

        {props.showExamples &&
          EXAMPLE_QUERIES.map((query) => (
            <button
              key={query}
              className="chip"
              onClick={() => props.onPickExample(query)}
            >
              {query}
            </button>
          ))}
      </div>

      {showAdvanced && (
        <div className="search__controls">
          <label>
            Bán kính{' '}
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
        </div>
      )}
    </>
  );
}

SearchForm.Filters = Filters;
