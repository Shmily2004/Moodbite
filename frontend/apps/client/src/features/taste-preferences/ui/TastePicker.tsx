/**
 * "Sở thích của bạn" — chọn vài khẩu vị để lần sau khỏi phải lọc lại từ đầu.
 *
 * ⚠️ MỖI Ô CHỌN PHẢI LÀ MỘT GIÁ TRỊ BACKEND HIỂU ĐƯỢC.
 * Bản thiết kế vẽ "Đồ nướng · Món cay · Món Hàn · Healthy · Trà sữa". Ba cái đầu ánh xạ
 * được vào bộ lọc thật (cách chế biến / mood cay / ẩm thực); "Healthy" và "Trà sữa" thì
 * KHÔNG có gì phía sau để lọc, nên không đưa vào — một ô sở thích bấm xong mà kết quả
 * không đổi thì tệ hơn là không có.
 *
 * ⚠️ LƯU Ở TRÌNH DUYỆT. Backend chưa có bảng "sở thích người dùng" và cũng chưa có
 * endpoint nào đọc/ghi. Làm ở server là ĐỔI LƯỢC ĐỒ DỮ LIỆU — việc phải chốt trước
 * (CLAUDE.md mục 8). Bản localStorage này đổi lại được ngay và nói đúng thứ nó làm.
 */
import type { UseTastePreferencesResult } from '../model/useTastePreferences';
import { SO_THICH } from '../model/danh_sach';
import { useT } from '@/shared/i18n';

export interface TastePickerProps {
  /**
   * State sở thích do TRANG giữ (đổi 2026-09-16). Trước đó component tự gọi
   * `useTastePreferences()`, nên biểu đồ "Khẩu vị của bạn" cùng trang giữ một bản state
   * RIÊNG và không đổi theo khi người dùng bấm chip — hai chỗ nói hai chuyện.
   */
  prefs: UseTastePreferencesResult;
}

export function TastePicker({ prefs }: TastePickerProps) {
  const t = useT();
  const { chon, dangChon, xoaHet, soLuong } = prefs;

  return (
    <section className="panel">
      <div className="results__head">
        <h2 className="panel__title">
          <span aria-hidden="true">🍽️</span> {t('account.taste.title')}
        </h2>
        {soLuong > 0 && (
          <button type="button" className="linkish" onClick={xoaHet}>
            {t('account.taste.clear')}
          </button>
        )}
      </div>
      <p className="section-sub">{t('account.taste.sub')}</p>

      <ul className="chip-row">
        {SO_THICH.map((mon) => {
          const bat = dangChon(mon.id);
          return (
            <li key={mon.id}>
              <button
                type="button"
                className={bat ? 'chip chip--on' : 'chip'}
                aria-pressed={bat}
                onClick={() => chon(mon.id)}
              >
                <span aria-hidden="true">{mon.emoji}</span> {mon.label}
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
