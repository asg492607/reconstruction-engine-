import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.VITE_API_BASE_URL || 'https://reconstruction-engine.onrender.com'

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/auth': { target, changeOrigin: true },
        '/cases': { target, changeOrigin: true },
        '/evidence': { target, changeOrigin: true },
        '/observations': { target, changeOrigin: true },
        '/entities': { target, changeOrigin: true },
        '/timelines': { target, changeOrigin: true },
        '/gaps-conflicts': { target, changeOrigin: true },
        '/findings': { target, changeOrigin: true },
        '/reconstruction': { target, changeOrigin: true },
        '/verification': { target, changeOrigin: true },
        '/copilot': { target, changeOrigin: true },
        '/reports': { target, changeOrigin: true },
        '/health': { target, changeOrigin: true },
        '/engines': { target, changeOrigin: true },
        '/ocr': { target, changeOrigin: true },
        '/department-engines': { target, changeOrigin: true },
      }
    }
  }
})
