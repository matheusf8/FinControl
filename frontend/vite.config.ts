/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // Em dev, o frontend (Vite, porta 5173) chama /api e isso é
      // encaminhado pro backend FastAPI (porta 8000). No .exe final,
      // ambos são servidos pela mesma origem, então esse proxy não é usado.
      '/api': 'http://localhost:8000',
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    globals: true,
  },
})
