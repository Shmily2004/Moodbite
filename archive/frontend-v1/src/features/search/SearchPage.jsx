import useUserLocation from '../map/useUserLocation'
import useSearch from './useSearch'
import RestaurantCard from './RestaurantCard'

/**
 * Trang tìm kiếm chính - component "thông minh": giữ state, điều phối, truyền props xuống.
 *
 * Đề án mục 2: người dùng GÕ NHU CẦU BẰNG CÂU TỰ NHIÊN thay vì bị ép chọn trong bộ lọc
 * cứng. Các nút mood bên dưới chỉ là lối tắt gợi ý, không phải cách dùng chính.
 */

const EXAMPLE_QUERIES = [
  'phở bò gần đây',
  'chỗ yên tĩnh để làm việc',
  'quán lẩu ấm cúng',
  'ăn gì đó nhẹ, tốt cho sức khoẻ',
]

const MOOD_SHORTCUTS = [
  { value: 'happy', label: '😊 Vui' },
  { value: 'sad', label: '😔 Buồn' },
  { value: 'excited', label: '🌶️ Hào hứng' },
  { value: 'relaxed', label: '☕ Thư giãn' },
]

export default function SearchPage() {
  const location = useUserLocation()
  const {
    queryText, setQueryText,
    maxDistanceKm, setMaxDistanceKm,
    results, context, warnings, searchQueryId,
    loading, error, run,
  } = useSearch({ position: location.position })

  const onSubmit = (e) => {
    e.preventDefault()
    run()
  }

  return (
    <div className="search">
      <form className="search__form" onSubmit={onSubmit}>
        <input
          className="search__input"
          type="text"
          value={queryText}
          onChange={(e) => setQueryText(e.target.value)}
          placeholder="Bạn muốn ăn gì? VD: quán lẩu ấm cúng gần đây"
          aria-label="Nhu cầu của bạn"
        />
        <button className="btn btn--primary" type="submit" disabled={loading}>
          {loading ? 'Đang tìm…' : 'Tìm'}
        </button>
      </form>

      <div className="search__examples">
        {EXAMPLE_QUERIES.map((q) => (
          <button key={q} className="chip" onClick={() => { setQueryText(q); run() }}>
            {q}
          </button>
        ))}
      </div>

      <div className="search__controls">
        <label>
          Bán kính:{' '}
          <select
            value={maxDistanceKm ?? ''}
            onChange={(e) => setMaxDistanceKm(e.target.value ? Number(e.target.value) : null)}
          >
            {[2, 5, 10, 20].map((km) => <option key={km} value={km}>{km} km</option>)}
            <option value="">Không giới hạn</option>
          </select>
        </label>

        <button className="btn" onClick={location.request} disabled={location.loading}>
          {location.loading ? 'Đang định vị…' : '📍 Dùng vị trí của tôi'}
        </button>

        <span className="muted">
          {location.isDefault ? 'Đang dùng trung tâm Hà Nội' : 'Đang dùng vị trí của bạn'}
        </span>
      </div>

      <div className="search__shortcuts">
        <span className="muted">Hoặc chọn nhanh:</span>
        {MOOD_SHORTCUTS.map((m) => (
          <button key={m.value} className="chip" onClick={() => run({ mood: m.value })}>
            {m.label}
          </button>
        ))}
      </div>

      {location.error && <p className="warn">{location.error}</p>}
      {error && <p className="error">{error}</p>}

      {context.length > 0 && (
        <p className="muted">Đang xét ngữ cảnh: {context.join(' · ')}</p>
      )}

      {/* Điều server KHÔNG làm được - hiện lên thay vì im lặng bỏ qua. */}
      {warnings.map((w, i) => <p key={i} className="warn">{w}</p>)}

      {loading && <p>Đang tìm…</p>}

      {results && results.length === 0 && !loading && (
        <p className="muted">Không tìm thấy quán nào. Thử mở rộng bán kính xem sao.</p>
      )}

      {results && results.length > 0 && (
        <ul className="results">
          {results.map((r) => (
            <RestaurantCard key={r.id ?? r.rankPosition} restaurant={r} searchQueryId={searchQueryId} />
          ))}
        </ul>
      )}
    </div>
  )
}
