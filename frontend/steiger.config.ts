import { defineConfig } from 'steiger';
import fsd from '@feature-sliced/steiger-plugin';

/**
 * Cưỡng chế luật import của Feature-Sliced Design.
 *
 * Đây là bản tương đương cho frontend của `scripts/check_architecture.py` bên backend:
 * kiến trúc TỰ BẢO VỆ, không phụ thuộc trí nhớ ai cả.
 */
export default defineConfig([
  ...fsd.configs.recommended,
  {
    // Áp dụng cho CẢ HAI app. Thêm app mới vào `apps/` là tự động được kiểm - không
    // phải nhớ sửa file này.
    files: ['./apps/*/src/**'],
    rules: {
      // Dự án còn nhỏ nên nhiều slice mới chỉ có 1 file và mới được 1 nơi dùng.
      // Tách nhỏ thêm lúc này chỉ tạo thư mục rỗng, chưa mang lại lợi ích gì.
      'fsd/insignificant-slice': 'off',
      'fsd/public-api': 'off',
    },
  },
]);
