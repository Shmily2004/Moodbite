/**
 * ĐẦU KHỐI KẾT QUẢ ở `/recommend`, theo `design/Filler.png`:
 *
 *   24 món ăn phù hợp                                   Sắp xếp: [Phù hợp nhất ▾]
 *   Đang lọc theo: [Trong vòng 3km ✕] [Tối ✕] [Trời mưa ✕]  Xoá tất cả
 *
 * Component "ngu": nhận dữ liệu và báo sự kiện lên `useRecommendPage`.
 *
 * ⚠️ Ô sắp xếp CHỈ có những kiểu làm được thật — xem `model/sapXepMon.ts`. API không có
 * tham số sort, nên không vẽ thêm "Gần nhất" / "Đánh giá cao": món không có toạ độ cũng
 * không có rating.
 */
import type { ChipDangBat } from '@/features/suggest-dishes';
import { IconClose, IconFilter } from '@/shared/ui';
import { useT } from '@/shared/i18n';
import { KIEU_SAP_XEP_MON } from '../model/sapXepMon';
import type { KieuSapXepMon } from '../model/sapXepMon';

const NHAN_SAP_XEP = {
  'phu-hop': 'recommend.sort.best',
  ten: 'recommend.sort.name',
  'so-quan': 'recommend.sort.restaurants',
} as const satisfies Record<KieuSapXepMon, string>;

interface ResultsToolbarProps {
  loading: boolean;
  count: number;
  chips: ChipDangBat[];
  onRemoveChip: (chip: ChipDangBat) => void;
  onClearAll: () => void;
  sort: KieuSapXepMon;
  onSortChange: (kieu: KieuSapXepMon) => void;
  /** Nút mở ngăn kéo — chỉ hiện ở màn hẹp, màn rộng đã có cột lọc bên trái. */
  onOpenFilters: () => void;
  activeFilterCount: number;
}

export function ResultsToolbar(props: ResultsToolbarProps) {
  const t = useT();

  return (
    <div className="ket-qua-dau">
      <div className="ket-qua-dau__hang">
        <h1 className="ket-qua-dau__tieu-de">
          {props.loading ? t('recommend.loading') : <TieuDeDem t={t} count={props.count} />}
        </h1>

        <div className="ket-qua-dau__cong-cu">
          <button
            type="button"
            className="btn btn--sm btn--filter ket-qua-dau__mo-loc"
            onClick={props.onOpenFilters}
          >
            <IconFilter /> {t('filters.open')}
            {props.activeFilterCount > 0 && (
              <span className="btn__badge">{props.activeFilterCount}</span>
            )}
          </button>

          <label className="ket-qua-dau__sap-xep">
            <span>{t('recommend.sortLabel')}</span>
            <select
              value={props.sort}
              onChange={(event) => props.onSortChange(event.target.value as KieuSapXepMon)}
            >
              {KIEU_SAP_XEP_MON.map((kieu) => (
                <option key={kieu} value={kieu}>
                  {t(NHAN_SAP_XEP[kieu])}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      {/* Chỉ hiện khi có gì đang lọc — dòng "Đang lọc theo:" trống trơn là nhiễu. */}
      {props.chips.length > 0 && (
        <div className="ket-qua-dau__dang-loc" role="group" aria-label={t('recommend.filteringBy')}>
          <span className="ket-qua-dau__nhan">{t('recommend.filteringBy')}</span>
          {props.chips.map((chip) => (
            <button
              key={chip.khoa}
              type="button"
              className="chip chip--active chip--go"
              onClick={() => props.onRemoveChip(chip)}
            >
              {chip.nhan}
              <IconClose className="chip__go" />
            </button>
          ))}
          <button type="button" className="linkish" onClick={props.onClearAll}>
            {t('recommend.clearAll')}
          </button>
        </div>
      )}
    </div>
  );
}

/**
 * "24 món ăn phù hợp" với CON SỐ tô cam cỡ lớn, phần chữ navy — đúng `design/Filler.png`.
 *
 * Tách câu dịch quanh chỗ `{count}` thay vì viết cứng "món ăn phù hợp": bản tiếng Anh
 * ("24 matching dishes") cũng tự đúng, và tên truy cập của tiêu đề vẫn là cả câu liền.
 */
function TieuDeDem({ t, count }: { t: ReturnType<typeof useT>; count: number }) {
  const [truoc, sau = ''] = t('recommend.title', { count: '{count}' }).split('{count}');
  return (
    <>
      {truoc}
      <span className="ket-qua-dau__so tnum">{count}</span>
      {sau}
    </>
  );
}
