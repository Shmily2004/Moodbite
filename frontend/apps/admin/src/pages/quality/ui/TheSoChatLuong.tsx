// Tách từ QualityPage.tsx ngày 2026-10-06 vì file vượt ~300 dòng (CLAUDE.md mục 6).
// Hàng thẻ số đầu trang. Giữ riêng trong slice này, không dùng chung `TheSo` với trang Tổng quan.
import { IconTron, type MauIconTron, type TenIcon } from '@/shared/ui';
import type { ThayDoi } from '@/shared/api';
import { soVN } from './soVN';

/**
 * Thẻ số CÓ so sánh với mốc quá khứ.
 *
 * `delta === null` -> nói "chưa đủ dữ liệu để so sánh". KHÔNG hiện mũi tên, KHÔNG hiện
 * "+0": cả hai đều nghe như đã so xong và kết luận là không đổi.
 */
export function TheSoCoMoc({
  nhan,
  thayDoi,
  icon,
  mau,
}: {
  nhan: string;
  thayDoi: ThayDoi;
  icon: TenIcon;
  mau: MauIconTron;
}) {
  const d = thayDoi.delta;

  return (
    <li className="the-so__o the-so__o--co-icon">
      <IconTron ten={icon} mau={mau} />
      <div className="the-so__than">
        <span className="the-so__nhan">{nhan}</span>
        <span className="the-so__gia-tri">{soVN(thayDoi.current)}</span>
        {d === null || d === undefined ? (
          <span className="muted the-so__phu">Chưa đủ dữ liệu để so sánh</span>
        ) : (
          <span
            className={
              d > 0 ? 'the-so__phu the-so__phu--tang' : 'muted the-so__phu'
            }
          >
            {d > 0 ? '↗ +' : d < 0 ? '↘ ' : ''}
            {d === 0 ? 'Không đổi' : soVN(Math.abs(d))}
            {d !== 0 && ' so với '}
            {d !== 0 &&
              thayDoi.baseline_date &&
              new Date(thayDoi.baseline_date).toLocaleDateString('vi-VN')}
          </span>
        )}
      </div>
    </li>
  );
}

export function TheSo({
  nhan,
  so,
  phu,
  icon,
  mau,
  nhanManh = false,
}: {
  nhan: string;
  so: number;
  phu?: string;
  icon: TenIcon;
  mau: MauIconTron;
  nhanManh?: boolean;
}) {
  return (
    <li
      className={
        nhanManh
          ? 'the-so__o the-so__o--co-icon the-so__o--nhan'
          : 'the-so__o the-so__o--co-icon'
      }
    >
      <IconTron ten={icon} mau={mau} />
      <div className="the-so__than">
        <span className="the-so__nhan">{nhan}</span>
        <span className="the-so__gia-tri">{soVN(so)}</span>
        {phu && <span className="muted the-so__phu">{phu}</span>}
      </div>
    </li>
  );
}
