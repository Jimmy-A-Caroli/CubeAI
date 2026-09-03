import { defineConfig } from 'vite';
import { configDefaults } from 'vitest/config';

export default defineConfig({
  server: {
    host: '127.0.0.1',
    proxy: {
      '/health': 'http://127.0.0.1:8000',
    },
  },
  test: {
    environment: 'jsdom',
    exclude: [...configDefaults.exclude],
    setupFiles: './src/test/setup.ts',
  },
});
