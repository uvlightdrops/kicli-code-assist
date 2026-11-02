import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const port = parseInt(process.env.VITE_PORT || '3000', 10)
const host = process.env.VITE_HOST || '127.0.0.1'
const apiUrl = process.env.VITE_API_URL || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    host,
    port,
    strictPort: false,
    proxy: {
      '/api': {
        target: apiUrl,
        changeOrigin: true,
      },
      '/socket.io': {
        target: apiUrl,
        ws: true,
      },
    },
  },
  build: {
    outDir: '../../../kicli-code-assist/web/static',
    emptyOutDir: true,
  },
  optimizeDeps: {
    exclude: ['monaco-vim'],
  },
})
