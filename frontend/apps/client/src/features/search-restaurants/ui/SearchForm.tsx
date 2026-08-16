/**
 * Ô tìm kiếm — component "NGU": chỉ nhận props và báo sự kiện lên trên.
 *
 * Đề án mục 2: người dùng GÕ NHU CẦU BẰNG CÂU TỰ NHIÊN thay vì bị ép chọn trong bộ lọc
 * cứng. Các nút mood bên dưới chỉ là lối tắt gợi ý, không phải cách dùng chính.
 */
import type { FormEvent } from 'react';

const EXAMPLE_QUERIES = [
  'phở bò gần đây',
  'chỗ yên tĩnh để làm việc',
  'quán lẩu ấm cúng',
  'ăn gì đó nhẹ, tốt cho sức khoẻ',
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
  maxDistanceKm: number | null;
  onMaxDistanceChange: (value: number | null) => void;
  openNow: boolean;
  onOpenNowChange: (value: boolean) => void;
  loading: boolean;
  locationIsDefault: boolean;
  locationLoading: boolean;
  onRequestLocation: () => void;
  onSubmit: () => void;
  onPickExample: (query: string) => void;
  onPickMood: (mood: string) => void;
}

export function SearchForm(props: SearchFormProps) {
  const submit = (event: FormEvent) => {
    event.preventDefault();
    props.onSubmit();
  };

  return (
    <section className="search">
      <form className="search__form" onSubmit={submit}>
        <input
          className="search__input"
          type="text"
          value={props.queryText}
          onChange={(event) => props.onQueryTextChange(event.target.value)}
          placeholder="Bạn muốn ăn gì? VD: quán lẩu ấm cúng gần đây"
          aria-label="Nhu cầu của bạn"
        />
        <button className="btn btn--primary" type="submit" disabled={props.loading}>
          {props.loading ? 'Đang tìm…' : 'Tìm'}
        </button>
      </form>

      <div className="search__examples">
        {EXAMPLE_QUERIES.map((query) => (
          <button key={query} className="chip" onClick={() => props.onPickExample(query)}>
            {query}
          </button>
        ))}
      </div>

      <div className="search__controls">
        <label>
          Bán kính:{' '}
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

        <label className="search__toggle">
          <input
            type="checkbox"
            checked={props.openNow}
            onChange={(event) => props.onOpenNowChange(event.target.checked)}
          />{' '}
          Đang mở cửa
        </label>

        <button
          className="btn"
          onClick={props.onRequestLocation}
          disabled={props.locationLoading}
        >
          {props.locationLoading ? 'Đang định vị…' : '📍 Dùng vị trí của tôi'}
        </button>

        <span className="muted">
          {props.locationIsDefault ? 'Đang dùng trung tâm Hà Nội' : 'Đang dùng vị trí của bạn'}
        </span>
      </div>

      <div className="search__shortcuts">
        <span className="muted">Hoặc chọn nhanh:</span>
        {MOOD_SHORTCUTS.map((mood) => (
          <button
            key={mood.value}
            className="chip"
            onClick={() => props.onPickMood(mood.value)}
          >
            {mood.label}
          </button>
        ))}
      </div>
    </section>
  );
}
