import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  plugins: [react()],
  // Cổng KHÁC app client (5173) để chạy song song được cả hai lúc phát triển.
  server: { port: 5174 },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
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
    // `afterEach` chạy THEO THỨ TỰ ĐĂNG KÝ, không đảo ngược (mặc định của vitest 2 là
    // 'stack' = đảo ngược). Bug thật 2026-09-29, đỏ ~1/10 lần chạy: `afterEach` của file
    // test (`vi.restoreAllMocks()`) chạy TRƯỚC cleanup của Testing Library, nên trong khe
    // hở đó promise của test vừa xong resolve, mount khối "Hoạt động", gọi `adminApi.
    // activity()` đã bị gỡ mock -> `undefined.then`. Lỗi đổ lên test ngẫu nhiên nên rất
    // khó lần. Với 'list', cleanup (đăng ký lúc import) unmount xong rồi mới gỡ mock.
    sequence: { hooks: 'list' },
  },
});
