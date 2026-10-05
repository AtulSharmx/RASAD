import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// dev mode: the API runs on :8000 (start.bat serves the built app from there directly)
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
})
