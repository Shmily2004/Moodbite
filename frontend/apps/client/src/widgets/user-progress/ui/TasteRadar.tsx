/**
 * Thẻ "KHẨU VỊ CỦA BẠN" — biểu đồ radar ở cột phải trang tài khoản (`design/profile.png`).
 *
 * CHỈ HIỂN THỊ: dữ liệu là những sở thích người dùng TỰ BẤM (localStorage), đếm theo nhóm ở
 * `features/taste-preferences/model/radar.ts`. Không có điểm khẩu vị nào do hệ thống đo.
 *
 * SVG thuần, không thư viện. `role="img"` + danh sách `sr-only` để trình đọc màn hình đọc
 * được đúng con số — một hình đa giác thì người khiếm thị không "nhìn" được.
 */
import type { TrucRadar } from '@/features/taste-preferences';
import { useT } from '@/shared/i18n';
import type { Khoa } from '@/shared/i18n';
import { chuoiDiem, diemTrenTruc, neoChu } from '../lib/hinhRadar';

const KICH_THUOC = 240;
const TAM = KICH_THUOC / 2;
/** Chừa lề cho nhãn trục nằm ngoài vòng ngoài cùng. */
const BAN_KINH = 70;
const CAC_VONG = [0.25, 0.5, 0.75, 1];

const NHAN_TRUC: Record<TrucRadar['nhom'], Khoa> = {
  cookingMethods: 'account.radar.axis.cookingMethods',
  temperatures: 'account.radar.axis.temperatures',
  mood: 'account.radar.axis.mood',
  cuisines: 'account.radar.axis.cuisines',
};

export interface TasteRadarProps {
  truc: TrucRadar[];
  /** Chuyển sang tab "Sở thích & khẩu vị". */
  onUpdate: () => void;
}

export function TasteRadar({ truc, onUpdate }: TasteRadarProps) {
  const t = useT();
  const soTruc = truc.length;
  const chuaChon = truc.every((x) => x.daChon === 0);

  return (
    <section className="panel taste-radar">
      <h2 className="panel__title">{t('account.radar.title')}</h2>

      {chuaChon || soTruc === 0 ? (
        <p className="section-sub">{t('account.radar.empty')}</p>
      ) : (
        <>
          <p className="section-sub">{t('account.radar.sub')}</p>
          <svg
            className="taste-radar__svg"
            viewBox={`0 0 ${KICH_THUOC} ${KICH_THUOC}`}
            role="img"
            aria-label={t('account.radar.title')}
          >
            {CAC_VONG.map((vong) => (
              <polygon
                key={vong}
                className="taste-radar__vong"
                points={chuoiDiem(
                  truc.map((_, i) => diemTrenTruc(i, soTruc, vong, TAM, BAN_KINH)),
                )}
              />
            ))}
            {truc.map((x, i) => {
              const dau = diemTrenTruc(i, soTruc, 1, TAM, BAN_KINH);
              const nhan = diemTrenTruc(i, soTruc, 1.28, TAM, BAN_KINH);
              return (
                <g key={x.nhom}>
                  <line className="taste-radar__truc" x1={TAM} y1={TAM} x2={dau.x} y2={dau.y} />
                  <text
                    className="taste-radar__nhan"
                    x={nhan.x}
                    y={nhan.y}
                    textAnchor={neoChu(nhan.x, TAM)}
                    dominantBaseline="middle"
                  >
                    {t(NHAN_TRUC[x.nhom])}
                  </text>
                </g>
              );
            })}
            <polygon
              className="taste-radar__vung"
              data-testid="taste-radar-vung"
              points={chuoiDiem(
                truc.map((x, i) => diemTrenTruc(i, soTruc, x.daChon / x.tong, TAM, BAN_KINH)),
              )}
            />
          </svg>
          <ul className="sr-only">
            {truc.map((x) => (
              <li key={x.nhom}>
                {t('account.radar.value', {
                  label: t(NHAN_TRUC[x.nhom]),
                  picked: x.daChon,
                  total: x.tong,
                })}
              </li>
            ))}
          </ul>
        </>
      )}

      <button type="button" className="btn btn--sm taste-radar__nut" onClick={onUpdate}>
        {t('account.radar.update')}
      </button>
    </section>
  );
}
