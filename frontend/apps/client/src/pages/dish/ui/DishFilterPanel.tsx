/**
 * Ngăn kéo bộ lọc của trang chi tiết món — CÙNG `FilterDrawer` + `DishFilters` với trang
 * chủ và trang gợi ý. Không có bản bộ lọc thứ hai: thêm/bớt một ô lọc chỉ sửa một chỗ.
 *
 * Chỉ mount khi mở (xem `useDishFilterPanel` để biết vì sao). Đóng mà không bấm
 * "Xem kết quả" thì bỏ các thay đổi — đúng như hành vi "huỷ" người dùng chờ đợi.
 */
import { FilterDrawer } from '@/widgets/filter-drawer';
import { DishFilters } from '@/features/suggest-dishes';
import type { DishItem } from '@/shared/api';
import { useT } from '@/shared/i18n';
import { useDishFilterPanel } from '../model/useDishFilterPanel';

interface DishFilterPanelProps {
  dish: DishItem | null;
  onClose: () => void;
  locationIsDefault: boolean;
  locationLoading: boolean;
  onRequestLocation: () => void;
}

export function DishFilterPanel({
  dish,
  onClose,
  locationIsDefault,
  locationLoading,
  onRequestLocation,
}: DishFilterPanelProps) {
  const t = useT();
  const boLoc = useDishFilterPanel(dish);

  return (
    <FilterDrawer
      open
      onClose={onClose}
      activeCount={boLoc.activeFilterCount}
      onReset={boLoc.reset}
      onApply={boLoc.apply}
    >
      <p className="section-sub">{t('dish.filtersSub')}</p>
      <DishFilters
        filters={boLoc.filters}
        onToggle={boLoc.toggle}
        onSetSingle={boLoc.setSingle}
        onSetMaxDistanceKm={boLoc.setMaxDistanceKm}
        onSetOnlyWithPrice={boLoc.setOnlyWithPrice}
        onReset={boLoc.reset}
        activeFilterCount={boLoc.activeFilterCount}
        locationIsDefault={locationIsDefault}
        locationLoading={locationLoading}
        onRequestLocation={onRequestLocation}
      />
    </FilterDrawer>
  );
}
