/**
 * Nút ĐĂNG XUẤT có hỏi lại. Dùng ở mọi nơi có nút đăng xuất của app người dùng.
 *
 * VÌ SAO HỎI LẠI: đăng xuất xong là mất phiên, phải gõ lại mật khẩu. Nút nằm sát các mục
 * khác trên thanh đầu trang nên dễ bấm nhầm. Hộp xác nhận rẻ hơn nhiều so với việc đăng
 * nhập lại.
 */
import { useCallback, useState, type ReactNode } from 'react';
import { ConfirmDialog } from '@/shared/ui';
import { useT } from '@/shared/i18n';

export interface LogoutButtonProps {
  onConfirm: () => void;
  className?: string;
  children: ReactNode;
}

export function LogoutButton({ onConfirm, className, children }: LogoutButtonProps) {
  const t = useT();
  const [dangHoi, setDangHoi] = useState(false);
  const huy = useCallback(() => setDangHoi(false), []);
  const dongY = useCallback(() => {
    setDangHoi(false);
    onConfirm();
  }, [onConfirm]);

  return (
    <>
      <button type="button" className={className} onClick={() => setDangHoi(true)}>
        {children}
      </button>
      <ConfirmDialog
        open={dangHoi}
        title={t('logout.confirm.title')}
        message={t('logout.confirm.message')}
        confirmLabel={t('logout.confirm.yes')}
        cancelLabel={t('logout.confirm.no')}
        onConfirm={dongY}
        onCancel={huy}
      />
    </>
  );
}
