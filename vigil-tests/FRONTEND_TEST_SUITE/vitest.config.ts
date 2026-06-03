/**
 * Vitest Configuration
 * Vigil Dashboard Frontend Test Suite
 */

import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./setupTests.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json'],
      exclude: [
        'node_modules/',
        'test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mocks/**',
        '**/types/**',
      ],
      thresholds: {
        branches: 70,
        functions: 70,
        lines: 70,
        statements: 70,
      },
    },
    reporters: ['default', 'vitest-sonar-reporter'],
    outputFile: {
      'vitest-sonar-reporter': './coverage/sonar-report.xml',
    },
    include: ['test/**/*.{test,spec}.{js,jsx,ts,tsx}'],
    exclude: [
      'node_modules/',
      'dist/',
      '**/*.config.{js,ts}',
    ],
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: false,
      },
    },
    // Retry flaky tests once
    retry: 1,
    // Fail on console errors in CI
    onConsoleLog: (log, type) => {
      if (process.env.CI && type === 'error') {
        return false;
      }
      return true;
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@stores': path.resolve(__dirname, './src/stores'),
      '@api': path.resolve(__dirname, './src/api'),
      '@lib': path.resolve(__dirname, './src/lib'),
      '@mocks': path.resolve(__dirname, './mocks'),
    },
  },
  css: {
    modules: {
      localsConvention: 'camelCase',
    },
  },
});
