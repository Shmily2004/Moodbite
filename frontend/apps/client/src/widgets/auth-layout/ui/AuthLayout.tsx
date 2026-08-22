/**
 * KHUNG DÙNG CHUNG cho các trang tài khoản (đăng nhập, và sau này là đăng ký).
 *
 * Bố cục máy tính — hai cột, đúng bản thiết kế `frontend/design/Login - register.png`:
 *
 *     ┌──────────────────────────────────────────────────────┐
 *     │ [logo]                                    VI ▾   🌙  │
 *     │                                                      │
 *     │  Ăn gì ở Hà Nội,              ┌────────────────────┐  │
 *     │  tùy mood của bạn.            │  form (children)   │  │
 *     │  <lời giới thiệu>             │                    │  │
 *     │                               └────────────────────┘  │
 *     │  ~~~ tranh Hà Nội ~~~ 📍 Made for Hà Nội              │
 *     └──────────────────────────────────────────────────────┘
 *
 * VÌ SAO LÀ `widgets/` CHỨ KHÔNG PHẢI `app/layout/`: đây KHÔNG phải khung của cả app —
 * chỉ hai trang tài khoản dùng. `RootLayout` ở `app/` cố tình rất mỏng vì trang chính là
 * bản đồ tràn màn hình. Nhét khung này vào đó thì mọi trang khác phải gánh theo.
 *
 * LOGO lấy từ `shared/ui/BrandLogo` -> `shared/config/images.ts` -> `public/anh/logo.png`,
 * tức bản trong `design/attribute/`. Logo vẽ trong ảnh mẫu là bản CŨ, KHÔNG dùng.
 */
import type { CSSProperties, ReactNode } from 'react';
import { BrandLogo, IconHeart, IconPin, LanguageSelect } from '@/shared/ui';
import { ThemeToggle } from '@/features/switch-theme';
import { ANH_GIAO_DIEN } from '@/shared/config';

export interface AuthLayoutProps {
  /** Tiêu đề lớn ở nửa trái. Nhận ReactNode để nhấn được chữ "mood" bằng thẻ riêng. */
  heading?: ReactNode;
  /** Đoạn giới thiệu ngắn dưới tiêu đề. */
  intro?: ReactNode;
  /**
   * Tranh nền, khai bằng KHOÁ trong `ANH_GIAO_DIEN` chứ không truyền thẳng đường dẫn:
   * mọi ảnh của giao diện chỉ được khai ở MỘT chỗ (`shared/config/images.ts`), nếu không
   * thì đổi ảnh phải đi sửa từng trang.
   */
  scene?: 'nen_dang_nhap' | 'nen_dang_ky';
  /** Thẻ form đặt ở cột phải. */
  children: ReactNode;
}

export function AuthLayout({
  heading,
  intro,
  scene = 'nen_dang_nhap',
  children,
}: AuthLayoutProps) {
  const tranh = ANH_GIAO_DIEN[scene];

  return (
    // `data-scene` để CSS chỉnh riêng theo từng tranh (VD trang đăng ký không có tiêu đề
    // nên tranh được cao hơn). Dùng thuộc tính dữ liệu thay vì đẻ thêm class biến thể:
    // thêm tranh mới chỉ cần thêm một khối CSS, không phải sửa JSX.
    <div className="auth" data-scene={scene}>
      {/*
        KHUNG. Mọi thứ nằm trong đây, và nó KHÔNG kéo dài hết bề ngang màn hình.

        VÌ SAO: khung của bản thiết kế gần vuông (813×815). Trải bố cục ra hết một màn
        hình 1920×887 thì mọi thứ đều teo lại theo tỉ lệ — logo còn 19% bề ngang thay vì
        28%, thẻ form còn 28% thay vì 40%, tranh còn 54% thay vì 100%. Đó chính là chỗ
        chủ dự án thấy "sai" (2026-08-22).

        Bề ngang khung buộc theo CHIỀU CAO màn hình (xem `--khung` trong auth.css) nên
        khung luôn gần vuông như bản thiết kế, và mọi tỉ lệ bên trong khớp theo.
      */}
      <div className="auth__frame">
        <header className="auth__bar">
          <BrandLogo />
          <div className="auth__tools">
            <LanguageSelect />
            <ThemeToggle />
          </div>
        </header>

        <div className="auth__body">
          <section className="auth__hero">
            {heading && <h1 className="auth__heading">{heading}</h1>}
            {intro && <p className="auth__intro">{intro}</p>}
          </section>

          <section className="auth__panel">{children}</section>
        </div>

        <span className="auth__badge">
          <IconPin width={16} height={16} />
          Made for Hà Nội!
          <IconHeart className="auth__badge-heart" width={15} height={15} />
        </span>

        {tranh && (
          /*
            Tranh nền vẽ bằng CSS `background-image`, KHÔNG dùng thẻ <img>.

            VÌ SAO ĐỔI (2026-08-22): bản cũ dùng <img> kèm `onError` để ẩn ảnh khi tải
            hỏng. Nhưng `onError` chỉ cần nổ MỘT lần — ví dụ đúng lúc script chuẩn bị ảnh
            đang ghi đè file — là state nhớ luôn "ảnh hỏng" và trang MẤT NỀN cho tới khi
            tải lại. Chủ dự án gặp đúng lỗi này.

            Ảnh nền là thứ trang trí thuần tuý: `background-image` không có sự kiện lỗi,
            không giữ state, hỏng thì đơn giản là không vẽ gì — nền kem vẫn đẹp. Ít thứ
            hỏng được hơn thì tốt hơn.
          */
          <div
            className="auth__scene"
            style={{ backgroundImage: `url("${tranh.src}")` } as CSSProperties}
            aria-hidden="true"
          />
        )}
      </div>
    </div>
  );
}
