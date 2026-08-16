/**
 * Trang tìm kiếm — tầng `pages`: GHÉP các widget/feature lại, giữ state điều phối.
 *
 * Đây là component "THÔNG MINH" duy nhất của luồng này. Mọi thứ bên dưới đều nhận props.
 */
import { useState } from 'react';
import { RestaurantList } from '@/widgets/restaurant-list';
import { RestaurantMap } from '@/widgets/restaurant-map';
import { SearchForm } from '@/features/search-restaurants';
import { useSearch } from '@/features/search-restaurants';
import { useUserLocation } from '@/features/pick-location';

export function SearchPage() {
  const location = useUserLocation();
  const search = useSearch({ position: location.position });
  const [openNow, setOpenNow] = useState(false);
  const [showMap, setShowMap] = useState(true);

  const runSearch = (options: { mood?: string } = {}) =>
    void search.run({ ...options, openNow });

  const pickExample = (query: string) => {
    search.setQueryText(query);
    void search.run({ openNow });
  };

  const hasResults = (search.results?.length ?? 0) > 0;

  return (
    <div className="page">
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

      {location.error && <p className="warn">{location.error}</p>}
      {search.error && <p className="error">{search.error}</p>}

      {search.context.length > 0 && (
        <p className="muted">Đang xét ngữ cảnh: {search.context.join(' · ')}</p>
      )}

      {/* Điều server KHÔNG làm được — hiện lên thay vì im lặng bỏ qua. */}
      {search.warnings.map((warning, index) => (
        <p key={index} className="warn">
          {warning}
        </p>
      ))}

      {search.loading && <p>Đang tìm…</p>}

      {search.results && !hasResults && !search.loading && (
        <p className="muted">Không tìm thấy quán nào. Thử mở rộng bán kính xem sao.</p>
      )}

      {hasResults && (
        <>
          <div className="view-toggle">
            <button
              className={`chip ${showMap ? 'chip--active' : ''}`}
              onClick={() => setShowMap(true)}
            >
              🗺️ Bản đồ
            </button>
            <button
              className={`chip ${!showMap ? 'chip--active' : ''}`}
              onClick={() => setShowMap(false)}
            >
              📋 Danh sách
            </button>
          </div>

          {showMap && (
            <RestaurantMap
              restaurants={search.results!}
              center={location.position}
              userPosition={location.isDefault ? null : location.position}
            />
          )}

          <RestaurantList
            restaurants={search.results!}
            searchQueryId={search.searchQueryId}
          />
        </>
      )}
    </div>
  );
}
