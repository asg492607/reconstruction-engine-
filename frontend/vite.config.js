import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/auth': 'http://127.0.0.1:8000',
      '/cases': 'http://127.0.0.1:8000',
      '/evidence': 'http://127.0.0.1:8000',
      '/observations': 'http://127.0.0.1:8000',
      '/entities': 'http://127.0.0.1:8000',
      '/timelines': 'http://127.0.0.1:8000',
      '/gaps-conflicts': 'http://127.0.0.1:8000',
      '/findings': 'http://127.0.0.1:8000',
      '/reconstruction': 'http://127.0.0.1:8000',
      '/verification': 'http://127.0.0.1:8000',
      '/copilot': 'http://127.0.0.1:8000',
      '/reports': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
      '/engines': 'http://127.0.0.1:8000',
    }
  }
})
