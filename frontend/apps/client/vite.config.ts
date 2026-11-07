import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      // Package dùng chung được alias thẳng tới mã nguồn TypeScript, không cần build
      // riêng - đơn giản hơn và vẫn giữ được kiểm tra kiểu xuyên package.
      '@moodbite/api-client': fileURLToPath(
        new URL('../../packages/api-client/src/index.ts', import.meta.url),
      ),
      '@moodbite/ui': fileURLToPath(
        new URL('../../packages/ui/src/index.ts', import.meta.url),
      ),
      // Khu QUẢN TRỊ (gộp 2026-11-01) là package riêng nằm cạnh app này. Alias `@admin` dành
      // cho nội bộ package (tránh đụng `@/` của app người dùng); `@moodbite/admin` là API công khai.
      '@admin': fileURLToPath(new URL('../../packages/admin/src', import.meta.url)),
      '@moodbite/admin': fileURLToPath(
        new URL('../../packages/admin/src/index.ts', import.meta.url),
      ),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/shared/test/setup.ts',
    // Test của khu quản trị nằm trong package `packages/admin` nên phải khai thêm đường dẫn.
    include: [
      'src/**/*.{test,spec}.{ts,tsx}',
      '../../packages/admin/src/**/*.{test,spec}.{ts,tsx}',
    ],
    // `afterEach` chạy theo thứ tự đăng ký: cleanup của Testing Library unmount xong rồi
    // mới tới `vi.restoreAllMocks()` của file test. Mặc định 'stack' đảo ngược thứ tự đó
    // và đã gây test chập chờn thật ở khu quản trị (2026-09-29).
    sequence: { hooks: 'list' },
  },
});
