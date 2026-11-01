/**
 * Thay cho trang tài khoản khi người đăng nhập là QUẢN TRỊ VIÊN.
 *
 * Trang tài khoản của app người dùng (hồ sơ, yêu thích, cấp độ, bộ sưu tập) được thiết kế
 * cho khách hàng. Quản trị viên đăng nhập ở đây nhầm chỗ, nên không hiện các mục đó mà chỉ
 * dẫn sang app quản trị — nơi việc của họ nằm.
 */
import { useT } from '@/shared/i18n';

export interface AdminAccountNoticeProps {
  href: string;
}

export function AdminAccountNotice({ href }: AdminAccountNoticeProps) {
  const t = useT();
  return (
    <section className="panel" aria-labelledby="tai-khoan-quan-tri">
      <h2 id="tai-khoan-quan-tri" className="panel__title">
        {t('account.admin.title')}
      </h2>
      <p>{t('account.admin.body')}</p>
      <p>
        <a className="btn" href={href} target="_blank" rel="noopener noreferrer">
          {t('account.admin.open')}
        </a>
      </p>
    </section>
  );
}
