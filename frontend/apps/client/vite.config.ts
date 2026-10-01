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
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/shared/test/setup.ts',
    // `afterEach` chạy theo thứ tự đăng ký: cleanup của Testing Library unmount xong rồi
    // mới tới `vi.restoreAllMocks()` của file test. Mặc định 'stack' đảo ngược thứ tự đó
    // và đã gây test chập chờn thật ở app admin (2026-09-29) - xem apps/admin/vite.config.ts.
    sequence: { hooks: 'list' },
  },
});
