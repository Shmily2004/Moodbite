/**
 * VIEW của việc báo quán đã đóng cửa. Chỉ JSX + gọi hook, không tự gọi API.
 *
 * HAI BƯỚC CÓ CHỦ ĐÍCH (bấm -> xác nhận -> gửi): một phiếu báo đóng cửa góp phần làm
 * quán BIẾN MẤT khỏi kết quả của mọi người. Bấm nhầm một lần trên điện thoại không được
 * phép gây ra chuyện đó, nên phải hỏi lại. Đây là quy tắc GIAO DIỆN, không phải nghiệp vụ.
 */
import { useState } from 'react';
import { useClosureReport } from '../model/useClosureReport';
import { useT } from '@/shared/i18n';

interface ReportClosureButtonProps {
  restaurantId: string;
  restaurantName: string;
}

export function ReportClosureButton({
  restaurantId,
  restaurantName,
}: ReportClosureButtonProps) {
  const { state, report } = useClosureReport();
  const [dangHoiLai, setDangHoiLai] = useState(false);
  const t = useT();

  if (state === 'sent') {
    return (
      <p className="closure closure--sent" role="status">
        {t('closure.sent')}
      </p>
    );
  }

  if (state === 'failed') {
    return (
      <p className="closure closure--failed" role="status">
        {t('closure.failed')}{' '}
        <button className="btn btn--link" onClick={() => void report(restaurantId)}>
          {t('closure.retry')}
        </button>
      </p>
    );
  }

  if (dangHoiLai) {
    return (
      <div className="closure closure--confirm">
        <span>
          {t('closure.confirmBefore')} <strong>{restaurantName}</strong> {t('closure.confirmAfter')}
        </span>
        <span className="closure__actions">
          <button
            className="btn btn--link closure__yes"
            disabled={state === 'sending'}
            onClick={() => void report(restaurantId)}
          >
            {state === 'sending' ? t('closure.sending') : t('closure.yes')}
          </button>
          <button className="btn btn--link" onClick={() => setDangHoiLai(false)}>
            {t('closure.cancel')}
          </button>
        </span>
      </div>
    );
  }

  return (
    <button className="btn btn--link closure__open" onClick={() => setDangHoiLai(true)}>
      {t('closure.open')}
    </button>
  );
}
