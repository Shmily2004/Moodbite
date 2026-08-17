/**
 * Trang tìm quán — tầng `pages`: GHÉP các widget/feature, giữ state điều phối.
 *
 * BỐ CỤC (chốt với chủ dự án 2026-08-17):
 *   thanh trên (thương hiệu + ô tìm) → hàng chip lọc → [ BẢN ĐỒ | RAIL ĐỀ XUẤT ]
 *
 * Bản đồ CỐ TÌNH không chiếm cả màn hình. MoodBite không phải Google Maps clone: khi
 * người dùng gõ "quán lẩu ấm cúng gần đây", thứ họ cần thấy trước là QUÁN NÀO PHÙ HỢP,
 * không phải bản đồ. Rail đề xuất vì thế luôn hiện, không phải kéo lên mới thấy.
 *
 * Bản đồ và rail nối HAI CHIỀU: bấm ghim → thẻ sáng lên và cuộn tới; bấm thẻ → ghim to ra.
 */
import { useEffect, useRef, useState } from 'react';
import { RestaurantList } from '@/widgets/restaurant-list';
import { RestaurantMap } from '@/widgets/restaurant-map';
import { SearchForm, useSearch } from '@/features/search-restaurants';
import { useUserLocation } from '@/features/pick-location';

export function SearchPage() {
  const location = useUserLocation();
  const search = useSearch({ position: location.position });
  const [openNow, setOpenNow] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);

  const listRef = useRef<HTMLDivElement>(null);

  const results = search.results ?? [];
  const hasResults = results.length > 0;

  const runSearch = (options: { mood?: string } = {}) => {
    setActiveId(null);
    void search.run({ ...options, openNow });
  };

  const pickExample = (query: string) => {
    search.setQueryText(query);
    setActiveId(null);
    void search.run({ openNow });
  };

  /** Mở rộng bán kính rồi tìm lại - lối thoát khi không có kết quả nào. */
  const widenRadius = () => {
    search.setMaxDistanceKm(20);
    setActiveId(null);
    void search.run({ openNow });
  };

  useEffect(() => {
    if (!activeId || !listRef.current) return;
    const node = listRef.current.querySelector(`[data-id="${CSS.escape(activeId)}"]`);
    node?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }, [activeId]);

  return (
    <div className="shell">
      <header className="topbar">
        <span className="brand">
          <span className="brand__dot" />
          <span className="brand__name">MoodBite</span>
        </span>

        <SearchForm
          queryText={search.queryText}
          onQueryTextChange={search.setQueryText}
          loading={search.loading}
          onSubmit={() => runSearch()}
        />

        {search.context.length > 0 && (
          <span className="topbar__ctx">{search.context.join(' · ')}</span>
        )}
      </header>

      <div className="filterbar">
        <SearchForm.Filters
          maxDistanceKm={search.maxDistanceKm}
          onMaxDistanceChange={search.setMaxDistanceKm}
          openNow={openNow}
          onOpenNowChange={setOpenNow}
          locationIsDefault={location.isDefault}
          locationLoading={location.loading}
          onRequestLocation={location.request}
          onPickMood={(mood) => runSearch({ mood })}
          onPickExample={pickExample}
          showExamples={!search.queryText}
        />
      </div>

      <div className="main">
        <div className="map-pane">
          <RestaurantMap
            restaurants={results}
            center={location.position}
            userPosition={location.isDefault ? null : location.position}
            activeId={activeId}
            onSelect={(restaurant) => setActiveId(restaurant.restaurant_id ?? null)}
          />
        </div>

        <section className="rail">
          <div className="rail__head">
            <span className="rail__count">
              {search.loading
                ? 'Đang tìm…'
                : hasResults
                  ? `${results.length} quán phù hợp`
                  : 'Kết quả đề xuất'}
            </span>
            {location.isDefault && (
              <span className="muted small">Trung tâm Hà Nội</span>
            )}
          </div>

          <div className="rail__body" ref={listRef}>
            {location.error && <p className="notice notice--warn">{location.error}</p>}
            {search.error && <p className="notice notice--error">{search.error}</p>}

            {/* Điều server KHÔNG làm được — hiện lên thay vì im lặng bỏ qua. */}
            {search.warnings.map((warning, index) => (
              <p key={index} className="notice notice--warn">
                {warning}
              </p>
            ))}

            {search.loading && <LoadingSkeleton />}

            {!search.loading && search.results && !hasResults && (
              <div className="state">
                <p className="state__title">Không tìm thấy quán nào</p>
                <p>Thử nới điều kiện xem sao.</p>
                <div className="state__fixes">
                  <button className="chip" onClick={widenRadius}>
                    Mở rộng 20 km
                  </button>
                  {openNow && (
                    <button
                      className="chip"
                      onClick={() => {
                        setOpenNow(false);
                        void search.run({ openNow: false });
                      }}
                    >
                      Bỏ lọc "đang mở"
                    </button>
                  )}
                </div>
              </div>
            )}

            {!search.loading && !search.results && !search.error && (
              <div className="state">
                <p className="state__title">Bạn đang muốn ăn gì?</p>
                <p>Gõ một câu bất kỳ — VD "quán lẩu ấm cúng gần đây".</p>
              </div>
            )}

            {hasResults && (
              <RestaurantList
                restaurants={results}
                searchQueryId={search.searchQueryId}
                queryText={search.queryText}
                activeId={activeId}
                onActivate={(id) => setActiveId(id)}
              />
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

/** Vệt xương lúc đang tải — báo "sắp có nội dung" thay vì để rail trống trơn. */
function LoadingSkeleton() {
  return (
    <div aria-busy="true" aria-label="Đang tìm quán">
      {[0, 1, 2, 3].map((i) => (
        <div className="skeleton" key={i}>
          <div className="skeleton__box" />
          <div>
            <div className="skeleton__line" />
            <div className="skeleton__line skeleton__line--short" />
            <div className="skeleton__line skeleton__line--short" />
          </div>
        </div>
      ))}
    </div>
  );
}
