/**
 * Trang tìm quán — tầng `pages`: GHÉP các widget/feature, giữ state điều phối.
 *
 * BỐ CỤC BẢN ĐỒ LÀ NỀN:
 *   - lớp dưới : bản đồ tràn kín màn hình
 *   - lớp trên : panel kết quả (cột trái trên máy tính, tấm trượt từ đáy trên điện thoại)
 *
 * Bản đồ và danh sách NỐI HAI CHIỀU: bấm ghim → thẻ được tô sáng và cuộn tới;
 * bấm thẻ → ghim tương ứng phóng to. Đây là điểm khiến giao diện "giống bản đồ thật"
 * chứ không phải một danh sách có kèm ảnh bản đồ.
 */
import { useEffect, useRef, useState } from 'react';
import type { SearchResultItem } from '@moodbite/api-client';
import { RestaurantList } from '@/widgets/restaurant-list';
import { RestaurantMap } from '@/widgets/restaurant-map';
import { SearchForm, useSearch } from '@/features/search-restaurants';
import { useUserLocation } from '@/features/pick-location';

export function SearchPage() {
  const location = useUserLocation();
  const search = useSearch({ position: location.position });
  const [openNow, setOpenNow] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

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

  /** Chọn từ bản đồ -> mở tấm trượt và cuộn tới đúng thẻ. */
  const selectFromMap = (restaurant: SearchResultItem) => {
    setActiveId(restaurant.restaurant_id ?? null);
    setExpanded(true);
  };

  // Cuộn tới thẻ đang chọn. Chỉ chạy khi activeId đổi, không chạy mỗi lần render.
  useEffect(() => {
    if (!activeId || !listRef.current) return;
    const node = listRef.current.querySelector(`[data-id="${CSS.escape(activeId)}"]`);
    node?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }, [activeId]);

  return (
    <div className="shell">
      <div className="map-layer">
        <RestaurantMap
          restaurants={results}
          center={location.position}
          userPosition={location.isDefault ? null : location.position}
          activeId={activeId}
          onSelect={selectFromMap}
        />
      </div>

      <div className="brand">
        <span className="brand__dot" />
        MoodBite
      </div>

      <section className={expanded ? 'panel panel--expanded' : 'panel'}>
        {/* Chỉ hiện trên điện thoại (CSS ẩn ở máy tính). */}
        <button
          className="panel__handle"
          onClick={() => setExpanded((open) => !open)}
          aria-expanded={expanded}
        >
          {expanded ? 'Thu gọn' : 'Kéo lên để xem danh sách'}
        </button>

        <div className="panel__head">
          <SearchForm
            queryText={search.queryText}
            onQueryTextChange={search.setQueryText}
            maxDistanceKm={search.maxDistanceKm}
            onMaxDistanceChange={search.setMaxDistanceKm}
            openNow={openNow}
            onOpenNowChange={setOpenNow}
            loading={search.loading}
            locationIsDefault={location.isDefault}
            locationLoading={location.loading}
            onRequestLocation={location.request}
            onSubmit={() => runSearch()}
            onPickExample={pickExample}
            onPickMood={(mood) => runSearch({ mood })}
          />
        </div>

        <div className="panel__body" ref={listRef}>
          {location.error && <p className="notice notice--warn">{location.error}</p>}
          {search.error && <p className="notice notice--error">{search.error}</p>}

          {search.context.length > 0 && (
            <p className="notice notice--info">
              Đang xét: {search.context.join(' · ')}
            </p>
          )}

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
              <p>Thử mở rộng bán kính trong Bộ lọc, hoặc gõ nhu cầu khác.</p>
            </div>
          )}

          {!search.loading && !search.results && (
            <div className="state">
              <p className="state__title">Bạn đang muốn ăn gì?</p>
              <p>Gõ một câu bất kỳ, hoặc chọn nhanh một gợi ý ở trên.</p>
            </div>
          )}

          {hasResults && (
            <RestaurantList
              restaurants={results}
              searchQueryId={search.searchQueryId}
              activeId={activeId}
              onActivate={(id) => setActiveId(id)}
            />
          )}
        </div>
      </section>
    </div>
  );
}

/** Vệt xương lúc đang tải — báo "sắp có nội dung" thay vì để panel trống trơn. */
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
