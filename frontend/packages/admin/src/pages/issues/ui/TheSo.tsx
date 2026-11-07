import { IconTron, type MauIconTron, type TenIcon } from '@admin/shared/ui';
import { soVN } from './hienThi';

export function TheSo({
  nhan,
  so,
  phu,
  icon,
  mau,
}: {
  nhan: string;
  so: number;
  phu?: string;
  icon: TenIcon;
  mau: MauIconTron;
}) {
  return (
    <li className="the-so__o the-so__o--co-icon">
      <IconTron ten={icon} mau={mau} />
      <div className="the-so__than">
        <span className="the-so__nhan">{nhan}</span>
        <span className="the-so__gia-tri">{soVN(so)}</span>
        {phu && <span className="muted the-so__phu">{phu}</span>}
      </div>
    </li>
  );
}
