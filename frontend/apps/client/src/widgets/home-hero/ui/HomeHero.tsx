/**
 * Khối MỞ ĐẦU trang chủ: lời chào · khẩu hiệu · tín hiệu ngữ cảnh · ô tìm · tranh minh hoạ.
 *
 * ⚠️ CÁC "CHIP" NGỮ CẢNH LÀ DỮ LIỆU THẬT, KHÔNG PHẢI TRANG TRÍ.
 * Chúng lấy nguyên văn từ mảng `context` mà `/dishes/suggest` trả về (giờ ăn, thời tiết).
 * Bản thiết kế vẽ sẵn "28°C trời mưa nhẹ · Đồ nướng · Món nóng"; ta KHÔNG viết cứng mấy
 * chuỗi đó — hôm trời nắng mà vẫn hiện "trời mưa" thì cả trang mất tin cậy. Thời tiết chỉ
 * có khi bật `MOODBITE_ENABLE_WEATHER=1`; không có thì chip đó đơn giản là không hiện.
 */
import { useState } from 'react';
import type { FormEvent } from 'react';
import { ANH_GIAO_DIEN } from '@/shared/config';
import { Slogan } from '@/shared/ui';

export interface HomeHeroProps {
  /** Tên hiển thị của người đang đăng nhập, hoặc `null` khi chưa đăng nhập. */
  userName: string | null;
  /** Câu ngữ cảnh backend trả về, VD "trời mưa", "bữa trưa". */
  context: string[];
  /** Gọi khi người dùng bấm "Tìm ngay" với ô nhập khác rỗng. */
  onSearch: (query: string) => void;
}

/**
 * Lời chào theo giờ máy người dùng.
 *
 * Đây là QUY TẮC HIỂN THỊ thuần tuý nên đặt ở frontend là đúng chỗ — nó không đổi kết quả
 * gợi ý nào. (Giờ ăn dùng để CHẤM ĐIỂM món thì ngược lại, do backend quyết.)
 */
function loiChao(gio: number): string {
  if (gio < 11) return 'Chào buổi sáng';
  if (gio < 14) return 'Chào buổi trưa';
  if (gio < 18) return 'Chào buổi chiều';
  return 'Chào buổi tối';
}

export function HomeHero({ userName, context, onSearch }: HomeHeroProps) {
  const [query, setQuery] = useState('');
  const tranh = ANH_GIAO_DIEN.banner_trang_chu;

  const guiTim = (event: FormEvent) => {
    event.preventDefault();
    const chu = query.trim();
    if (chu) onSearch(chu);
  };

  return (
    <section className="hero">
      <div className="hero__text">
        <p className="hero__greeting">
          <span aria-hidden="true">👋</span> {loiChao(new Date().getHours())}
          {userName ? `, ${userName}` : ''}
        </p>

        <h1 className="hero__slogan">
          <Slogan />
        </h1>

        <p className="hero__intro">
          MoodBite gợi ý những món ăn phù hợp với cảm xúc, thời tiết và thời điểm của bạn.
        </p>

        {context.length > 0 && (
          <ul className="hero__signals" aria-label="Ngữ cảnh đang được dùng để gợi ý">
            {context.map((tin) => (
              <li key={tin} className="signal">
                {tin}
              </li>
            ))}
          </ul>
        )}

        <form className="hero__search" onSubmit={guiTim} role="search">
          <label className="sr-only" htmlFor="hero-search">
            Tìm món ăn hoặc quán ăn
          </label>
          <input
            id="hero-search"
            className="hero__search-input"
            value={query}
            placeholder="Tìm món ăn, quán ăn, món bạn muốn…"
            onChange={(event) => setQuery(event.target.value)}
          />
          <button type="submit" className="btn btn--accent" disabled={query.trim() === ''}>
            Tìm ngay
          </button>
        </form>
      </div>

      {tranh && (
        /* Tranh trang trí: `aria-hidden` để trình đọc màn hình bỏ qua, không đọc một ô
           trống vô nghĩa. Vẽ bằng thẻ <img> (không phải nền CSS) để nó co theo bố cục. */
        <img
          className="hero__art"
          src={tranh.src}
          alt=""
          width={tranh.width}
          height={tranh.height}
          aria-hidden="true"
        />
      )}
    </section>
  );
}
