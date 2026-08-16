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
    files: ['./apps/client/src/**'],
    rules: {
      // Dự án còn nhỏ nên nhiều slice mới chỉ có 1 file - chưa cần tách thêm.
      'fsd/insignificant-slice': 'off',
      'fsd/public-api': 'off',
    },
  },
]);
