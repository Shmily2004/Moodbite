/**
 * Ô chọn ngôn ngữ. Đổi ngay lập tức, nhớ lại ở lần mở sau (localStorage).
 *
 * ⚠️ Ô này CÓ `title` nói rõ giới hạn: giao diện dịch được, còn tên món/tên quán và mọi
 * chữ do máy chủ sinh ra vẫn là tiếng Việt. Nói trước vẫn hơn để người dùng bật tiếng Anh
 * rồi tự hỏi vì sao nửa trang không đổi. Muốn dịch nốt phần đó thì phải làm i18n Ở
 * BACKEND — việc riêng, xem ghi chú đầu `shared/i18n/model/tu_dien.ts`.
 */
import { NGON_NGU, useNgonNgu } from '../i18n';
import type { NgonNgu } from '../i18n';

const NHAN: Record<NgonNgu, string> = { vi: 'VI', en: 'EN' };

export function LanguageSelect({ className }: { className?: string }) {
  const { ngonNgu, doiNgonNgu, t } = useNgonNgu();

  return (
    <select
      className={['lang-select', className].filter(Boolean).join(' ')}
      value={ngonNgu}
      onChange={(su_kien) => doiNgonNgu(su_kien.target.value as NgonNgu)}
      aria-label={t('lang.label')}
      title={t('lang.hint')}
    >
      {NGON_NGU.map((ma) => (
        <option key={ma} value={ma}>
          {NHAN[ma]}
        </option>
      ))}
    </select>
  );
}
