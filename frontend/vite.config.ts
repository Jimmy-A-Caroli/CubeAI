import { defineConfig } from 'vite';
import { configDefaults } from 'vitest/config';

const localBackendUrl =
  process.env.CUBEAI_BACKEND_URL ?? 'http://127.0.0.1:8000';

export default defineConfig({
  server: {
    host: '127.0.0.1',
    proxy: {
      '/health': localBackendUrl,
      '/v1': localBackendUrl,
    },
  },
  test: {
    environment: 'jsdom',
    exclude: [...configDefaults.exclude],
    setupFiles: './src/test/setup.ts',
  },
});
