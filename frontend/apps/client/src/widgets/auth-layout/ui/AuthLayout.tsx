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
import { useState } from 'react';
import type { ReactNode } from 'react';
import { BrandLogo, IconPin, LanguageSelect } from '@/shared/ui';
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
  const [tranhHong, setTranhHong] = useState(false);

  return (
    // `data-scene` để CSS chỉnh riêng theo từng tranh (VD trang đăng ký không có tiêu đề
    // nên tranh được cao hơn). Dùng thuộc tính dữ liệu thay vì đẻ thêm class biến thể:
    // thêm tranh mới chỉ cần thêm một khối CSS, không phải sửa JSX.
    <div className="auth" data-scene={scene}>
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
          <span className="auth__badge">
            <IconPin width={16} height={16} />
            Made for Hà Nội
          </span>
        </section>

        <section className="auth__panel">{children}</section>
      </div>

      {tranh && !tranhHong && (
        <img
          className="auth__scene"
          src={tranh.src}
          alt={tranh.alt}
          width={tranh.width}
          height={tranh.height}
          // Sai tên file thì trình duyệt hiện ô ảnh vỡ. Ẩn hẳn đi: trang vẫn đẹp vì nền
          // kem và bố cục không phụ thuộc vào tấm tranh này.
          onError={() => setTranhHong(true)}
        />
      )}
    </div>
  );
}
