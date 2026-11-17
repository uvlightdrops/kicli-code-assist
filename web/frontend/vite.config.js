import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
var port = 5173;
var host = '127.0.0.1';
var apiUrl = 'http://127.0.0.1:8100';
export default defineConfig({
    plugins: [react()],
    server: {
        host: host,
        port: port,
        strictPort: true,
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
});
