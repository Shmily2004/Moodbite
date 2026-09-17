/**
 * THANH TRƯỢT BÁN KÍNH — component "ngu", dựng theo `design/Filler.png`.
 *
 * Dùng `<input type="range">` gốc của trình duyệt chứ không tự vẽ: nó có sẵn phím mũi tên,
 * đọc được bằng trình đọc màn hình và kéo được bằng cảm ứng — ba thứ một thanh trượt tự
 * chế thường quên. `aria-valuetext` để trình đọc màn hình nói "3 km" thay vì "1" (vị trí).
 *
 * Nấc và cách đổi vị trí <-> km nằm ở `model/khoangCach.ts`.
 */
import { useT } from '@/shared/i18n';
import { NAC_KHOANG_CACH, giaTriNac, viTriNac } from '../model/khoangCach';

interface DistanceSliderProps {
  value: number | null;
  onChange: (km: number | null) => void;
}

export function DistanceSlider({ value, onChange }: DistanceSliderProps) {
  const t = useT();
  const nhan = (km: number | null) =>
    km === null ? t('filters.unlimited') : t('common.km', { n: km });

  return (
    <div className="distance">
      <div className="distance__head">
        <span className="filters__label">{t('filters.distance')}</span>
        {/* Nhãn hiện GIÁ TRỊ THẬT, không phải nấc gần nhất — xem `viTriNac`. */}
        <strong className="distance__value">{nhan(value)}</strong>
      </div>
      <input
        className="distance__range"
        type="range"
        min={0}
        max={NAC_KHOANG_CACH.length - 1}
        step={1}
        value={viTriNac(value)}
        aria-label={t('filters.distance')}
        aria-valuetext={nhan(value)}
        onChange={(event) => onChange(giaTriNac(Number(event.target.value)))}
      />
      <ol className="distance__ticks" aria-hidden="true">
        {NAC_KHOANG_CACH.map((km) => (
          <li key={String(km)}>{km === null ? '∞' : `${km}`}</li>
        ))}
      </ol>
    </div>
  );
}
