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
});
