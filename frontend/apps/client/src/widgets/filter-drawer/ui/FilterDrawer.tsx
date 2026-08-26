/**
 * NGĂN KÉO BỘ LỌC — trượt từ mép phải.
 *
 * Chủ dự án chốt phương án A (2026-08-23) sau khi cân nhắc hai cách:
 *   A. nút "Lọc" cạnh tiêu đề kết quả -> mở ngăn kéo   <- ĐÃ CHỌN
 *   B. cột lọc cố định bên trái
 * Lý do chọn A: không bóp lưới món, và DÙNG CHUNG MỘT component cho cả máy tính lẫn điện
 * thoại — phương án B trên điện thoại vẫn phải làm ngăn kéo, tức là hai bản phải bảo trì.
 *
 * BỔ SUNG 2026-08-24 — thiết kế mới muốn cột trái kiểu TopCV. Chủ dự án chốt: giữ A làm
 * GỐC, nhưng cho phép ĐẶT CÙNG MỘT component vào cột trái ở màn rộng (`variant="inline"`).
 * Nhờ vậy vẫn đúng lý do chọn A ban đầu — chỉ có MỘT component để bảo trì — mà vẫn được
 * bố cục cột trái. Ai đó định tách thành hai component riêng thì đọc lại đoạn này trước.
 *
 * VÌ SAO KHÔNG PHẢI MỘT TRANG RIÊNG: chỉ có 21 điều khiển, và lọc là việc LẶP (bấm ->
 * nhìn kết quả -> bấm tiếp). Tách sang trang khác là cắt đứt vòng lặp đó.
 *
 * BỐN THỨ BẮT BUỘC CỦA MỘT HỘP THOẠI, thiếu cái nào cũng thành cái bẫy:
 *   1. `Esc` đóng được          — phản xạ của mọi người dùng bàn phím
 *   2. Bấm nền mờ đóng được     — phản xạ của mọi người dùng chuột/cảm ứng
 *   3. KHOÁ CUỘN TRANG NỀN      — không khoá thì cuộn trong ngăn kéo tới đáy sẽ kéo luôn
 *                                 trang phía sau, người dùng mất chỗ đang đứng
 *   4. TRẢ TIÊU ĐIỂM về nút mở  — nếu không, đóng xong tiêu điểm rơi về đầu trang và
 *                                 người dùng bàn phím phải Tab lại từ đầu
 */
import { useEffect, useRef } from 'react';
import type { ReactNode } from 'react';
import { useT } from '@/shared/i18n';

export interface FilterDrawerProps {
  /**
   * 'drawer' = hộp thoại trượt từ mép phải (mặc định, dùng cho màn hẹp).
   * 'inline' = khối gắn thẳng vào bố cục, KHÔNG có nền mờ, KHÔNG khoá cuộn, KHÔNG bẫy
   *            tiêu điểm — vì nó không phải hộp thoại, và làm mấy việc đó với một khối
   *            luôn hiển thị sẽ khoá cuộn trang vĩnh viễn.
   */
  variant?: 'drawer' | 'inline';
  open: boolean;
  onClose: () => void;
  /** Số bộ lọc đang bật — hiện ở tiêu đề để người dùng biết mình đang lọc gì đó. */
  activeCount: number;
  onReset: () => void;
  /**
   * Bấm nút "Xem kết quả" ở đáy. Không truyền thì chỉ ĐÓNG ngăn kéo.
   *
   * VÌ SAO TÁCH KHỎI `onClose` (2026-08-26): ở TRANG CHỦ, chọn xong bộ lọc thì phải sang
   * `/recommend` để xem danh sách đầy đủ — đóng ngăn kéo rồi vẫn đứng nguyên trang chủ
   * là cụt luồng, đúng chỗ chủ dự án chỉ ra. Còn ở chính `/recommend` thì đã đúng trang
   * rồi nên đóng là đủ — vì vậy tham số này TUỲ CHỌN chứ không bắt buộc.
   */
  onApply?: () => void;
  children: ReactNode;
}

export function FilterDrawer({
  variant = 'drawer',
  open,
  onClose,
  activeCount,
  onReset,
  onApply,
  children,
}: FilterDrawerProps) {
  const t = useT();
  const panelRef = useRef<HTMLDivElement>(null);
  // Nhớ phần tử đang có tiêu điểm TRƯỚC khi mở, để lúc đóng trả về đúng chỗ đó.
  const truocDo = useRef<HTMLElement | null>(null);

  useEffect(() => {
    // Bốn hành vi dưới đây CHỈ đúng với hộp thoại. Ở dạng `inline` khối này luôn hiển
    // thị, nên khoá cuộn trang sẽ khoá vĩnh viễn và `Esc` sẽ "đóng" một thứ không đóng
    // được — đó là lý do chặn ngay từ đây thay vì rải `if` khắp nơi.
    if (variant !== 'drawer' || !open) return;

    truocDo.current = document.activeElement as HTMLElement | null;
    // Đưa tiêu điểm vào trong ngăn kéo, nếu không trình đọc màn hình vẫn đang đọc trang
    // phía sau và người dùng không biết vừa có gì mở ra.
    panelRef.current?.focus();

    const cuonCu = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    const phim = (su_kien: KeyboardEvent) => {
      if (su_kien.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', phim);

    return () => {
      document.removeEventListener('keydown', phim);
      document.body.style.overflow = cuonCu;
      truocDo.current?.focus();
    };
  }, [variant, open, onClose]);

  // Dạng `inline`: luôn hiển thị, không có nền mờ, không có nút đóng.
  if (variant === 'inline') {
    return (
      <aside className="drawer drawer--inline" aria-label={t('filters.title')}>
        <div className="drawer__head">
          <h2 className="panel__title">
            {t('filters.title')}
            {activeCount > 0 && <span className="drawer__count">{activeCount}</span>}
          </h2>
          {activeCount > 0 && (
            <button type="button" className="linkish" onClick={onReset}>
              {t('results.clearFilters')}
            </button>
          )}
        </div>
        <div className="drawer__body">{children}</div>
      </aside>
    );
  }

  if (!open) return null;

  return (
    <div className="drawer">
      {/* Nền mờ. `aria-hidden` vì nó chỉ là lớp phủ; nội dung thật nằm ở panel bên cạnh. */}
      <div className="drawer__veil" onClick={onClose} aria-hidden="true" />

      <div
        className="drawer__panel"
        role="dialog"
        aria-modal="true"
        aria-label={t('filters.title')}
        tabIndex={-1}
        ref={panelRef}
      >
        <div className="drawer__head">
          <h2 className="panel__title">
            {t('filters.title')}
            {activeCount > 0 && <span className="drawer__count">{activeCount}</span>}
          </h2>
          <div className="drawer__head-actions">
            {activeCount > 0 && (
              <button type="button" className="linkish" onClick={onReset}>
                {t('results.clearFilters')}
              </button>
            )}
            <button
              type="button"
              className="drawer__close"
              onClick={onClose}
              aria-label={t('filters.close')}
            >
              ✕
            </button>
          </div>
        </div>

        <div className="drawer__body">{children}</div>

        {/* Nút "Xem kết quả" ở đáy: trên điện thoại, sau khi bấm vài chip người dùng
            không nhìn thấy danh sách nên không biết đã xong hay chưa. */}
        <div className="drawer__foot">
          <button
            type="button"
            className="btn btn--accent"
            onClick={onApply ?? onClose}
          >
            {t('filters.apply')}
          </button>
        </div>
      </div>
    </div>
  );
}
