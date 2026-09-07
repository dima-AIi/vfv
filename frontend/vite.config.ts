import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const apiTarget = process.env.DEVOS_API_TARGET ?? 'http://localhost:8000'

const proxy = {
  '/api': {
    target: apiTarget,
    changeOrigin: true,
  },
  '/docs': {
    target: apiTarget,
    changeOrigin: true,
  },
  '/openapi.json': {
    target: apiTarget,
    changeOrigin: true,
  },
}

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    proxy,
  },
  preview: {
    host: '127.0.0.1',
    port: 5273,
    proxy,
  },
})
