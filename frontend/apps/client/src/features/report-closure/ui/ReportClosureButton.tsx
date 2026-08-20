/**
 * VIEW của việc báo quán đã đóng cửa. Chỉ JSX + gọi hook, không tự gọi API.
 *
 * HAI BƯỚC CÓ CHỦ ĐÍCH (bấm -> xác nhận -> gửi): một phiếu báo đóng cửa góp phần làm
 * quán BIẾN MẤT khỏi kết quả của mọi người. Bấm nhầm một lần trên điện thoại không được
 * phép gây ra chuyện đó, nên phải hỏi lại. Đây là quy tắc GIAO DIỆN, không phải nghiệp vụ.
 */
import { useState } from 'react';
import { useClosureReport } from '../model/useClosureReport';

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

  if (state === 'sent') {
    return (
      <p className="closure closure--sent" role="status">
        Đã ghi nhận. Cảm ơn bạn — quán sẽ được ẩn khi có thêm người xác nhận.
      </p>
    );
  }

  if (state === 'failed') {
    return (
      <p className="closure closure--failed" role="status">
        Gửi không được, có thể do mất mạng. Bạn thử lại giúp nhé.{' '}
        <button className="btn btn--link" onClick={() => void report(restaurantId)}>
          Thử lại
        </button>
      </p>
    );
  }

  if (dangHoiLai) {
    return (
      <div className="closure closure--confirm">
        <span>
          Xác nhận <strong>{restaurantName}</strong> đã đóng cửa?
        </span>
        <span className="closure__actions">
          <button
            className="btn btn--link closure__yes"
            disabled={state === 'sending'}
            onClick={() => void report(restaurantId)}
          >
            {state === 'sending' ? 'Đang gửi…' : 'Đúng, đã đóng'}
          </button>
          <button className="btn btn--link" onClick={() => setDangHoiLai(false)}>
            Huỷ
          </button>
        </span>
      </div>
    );
  }

  return (
    <button className="btn btn--link closure__open" onClick={() => setDangHoiLai(true)}>
      Quán này đã đóng cửa?
    </button>
  );
}
