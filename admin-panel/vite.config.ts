import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'material-ui': ['@mui/material', '@mui/icons-material'],
          'react-vendor': ['react', 'react-dom'],
        }
      }
    }
  },
  server: {
    allowedHosts: ['.ngrok-free.app'], // allow any subdomain of ngrok
    host: true, // listen on all addresses
  },
})
