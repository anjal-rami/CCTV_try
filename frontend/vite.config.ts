import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiUrl = env.VITE_API_URL || 'http://127.0.0.1:8000'

  return {
    plugins: [react(), tailwindcss()],
    base: '/',
    server: {
      host: true,
      port: 5173,
      strictPort: false,
      allowedHosts: true,
      hmr: {
        overlay: false // Disables the full-screen red error overlay
      },
      watch: {
        usePolling: true
      },
      proxy: {
        '/api': {
          target: apiUrl,
          changeOrigin: true,
          secure: false,
        }
      }
    }
  }
})
