import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/auth': 'http://localhost:8000',
      '/cases': 'http://localhost:8000',
      '/evidence': 'http://localhost:8000',
      '/observations': 'http://localhost:8000',
      '/entities': 'http://localhost:8000',
      '/timelines': 'http://localhost:8000',
      '/gaps-conflicts': 'http://localhost:8000',
      '/findings': 'http://localhost:8000',
      '/reconstruction': 'http://localhost:8000',
      '/verification': 'http://localhost:8000',
      '/copilot': 'http://localhost:8000',
      '/reports': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    }
  }
})
