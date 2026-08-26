/**
 * BONG BÓNG TRỢ LÝ — mascot nổi ở góc màn hình, bấm vào thì mở bộ lọc.
 *
 * Dựng theo ảnh chủ dự án gửi 2026-08-25 (`design/attribute/mascot bubble.png`):
 * mascot bên trái, lời thoại phía trên, nút "Tinh chỉnh gợi ý" bên dưới.
 *
 * ⚠️ CHỈ ĐẶT Ở TRANG CÓ MÓN/QUÁN (chốt 2026-08-24). Trang đăng nhập, đăng ký, tài khoản
 * không có gì để lọc — bong bóng ở đó vừa là nút chết vừa che nút "Đăng ký" ở góc phải.
 * Vì vậy widget này KHÔNG tự gắn vào layout gốc; từng trang chủ động đặt nó.
 *
 * KHÔNG gọi API, KHÔNG giữ bộ lọc: chỉ báo lên trên là người dùng muốn mở bộ lọc. Trang
 * mới là nơi giữ trạng thái lọc — nếu bong bóng cũng giữ một bản thì hai chỗ sẽ lệch nhau.
 */
import { ANH_GIAO_DIEN } from '@/shared/config';
import { IconSparkle } from '@/shared/ui';
import { useT } from '@/shared/i18n';

export interface AssistantBubbleProps {
  /** Bấm vào thì mở ngăn kéo bộ lọc của trang đang xem. */
  onOpen: () => void;
  /** Số bộ lọc đang bật — hiện lên để người dùng biết mình đang lọc gì đó. */
  activeCount?: number;
}

export function AssistantBubble({ onOpen, activeCount = 0 }: AssistantBubbleProps) {
  const t = useT();
  const anh = ANH_GIAO_DIEN.mascot_bubble;

  return (
    <div className="bubble">
      {/*
        BỐ CỤC ĐÚNG THEO ẢNH MẪU (dựng lại lần hai, 2026-08-26):

            ⌒            ┌──────────────────────────┐
          (mascot)       │ Chưa đúng gu?            │
           bên TRÁI      │ Tinh chỉnh gợi ý nhé!    │
                         └──────────────────────────┘
            ┌─────────────────────────────────────┐
            │ ✦  Tinh chỉnh gợi ý               › │  ← nút TRẮNG, trải ngang
            └─────────────────────────────────────┘

        ⚠️ HAI LẦN LÀM SAI TRƯỚC ĐÓ, ghi lại để khỏi lặp:
          lần 1 — nhét mascot vào BÊN TRONG nút như một icon;
          lần 2 — để mascot bên PHẢI và làm nút NỀN TỐI.
        Đúng là: mascot đứng bên TRÁI cạnh lời thoại, nút nền TRẮNG nằm dưới cả hai.
      */}
      <div className="bubble__tren">
        {anh && (
          <img
            className="bubble__mascot"
            src={anh.src}
            alt=""
            width={96}
            height={111}
            loading="lazy"
          />
        )}

        {/* Lời thoại. `aria-hidden` vì nút bên dưới đã nói đủ nghĩa cho trình đọc màn
            hình; đọc cả hai thành ra lặp. */}
        <p className="bubble__thoai" aria-hidden="true">
          {t('bubble.hint')}
        </p>
      </div>

      <button type="button" className="bubble__nut" onClick={onOpen}>
        <IconSparkle className="bubble__spark" />
        <span className="bubble__nhan">{t('bubble.cta')}</span>
        {activeCount > 0 && <span className="bubble__dem">{activeCount}</span>}
        <span className="bubble__mui-ten" aria-hidden="true">
          ›
        </span>
      </button>
    </div>
  );
}
