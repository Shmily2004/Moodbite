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
import { useTastePreferences } from '../model/useTastePreferences';
import { SO_THICH } from '../model/danh_sach';

export function TastePicker() {
  const { chon, dangChon, xoaHet, soLuong } = useTastePreferences();

  return (
    <section className="account__block">
      <div className="results__head">
        <h2 className="section-title">
          <span aria-hidden="true">🍽️</span> Sở thích của bạn
        </h2>
        {soLuong > 0 && (
          <button type="button" className="linkish" onClick={xoaHet}>
            Xoá hết
          </button>
        )}
      </div>
      <p className="section-sub">
        Chọn vài thứ bạn hay ăn. MoodBite sẽ bật sẵn các bộ lọc này ở trang chủ.
      </p>

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
