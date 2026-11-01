/**
 * Hộp thoại XÁC NHẬN dùng chung cho cả app người dùng và app quản trị.
 *
 * Dùng cho thao tác dễ bấm nhầm (đăng xuất). Chỉ là khung và hành vi bàn phím; nhãn nút
 * truyền từ ngoài vào để mỗi app dịch theo ngôn ngữ của mình.
 *
 * - Nút "Huỷ" được focus sẵn: bấm Enter nhầm thì không mất phiên đăng nhập.
 * - Esc hoặc bấm nền ngoài = huỷ.
 * - Kiểu dáng ở CSS của từng app (class `xac-nhan__*`).
 */
import { useEffect, useRef } from 'react';

export interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  cancelLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel,
  cancelLabel,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const nutHuy = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    nutHuy.current?.focus();
    const bamPhim = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel();
    };
    window.addEventListener('keydown', bamPhim);
    return () => window.removeEventListener('keydown', bamPhim);
  }, [open, onCancel]);

  if (!open) return null;

  return (
    <div className="xac-nhan" onMouseDown={onCancel}>
      <div
        className="xac-nhan__hop"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="xac-nhan-tieu-de"
        aria-describedby="xac-nhan-noi-dung"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h2 id="xac-nhan-tieu-de" className="xac-nhan__tieu-de">
          {title}
        </h2>
        <p id="xac-nhan-noi-dung" className="xac-nhan__noi-dung">
          {message}
        </p>
        <div className="xac-nhan__nut">
          <button ref={nutHuy} type="button" className="ghost" onClick={onCancel}>
            {cancelLabel}
          </button>
          <button type="button" className="xac-nhan__dong-y" onClick={onConfirm}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
