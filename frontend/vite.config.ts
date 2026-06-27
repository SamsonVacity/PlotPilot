import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  base: '/moshu/',
  define: {
    'import.meta.env.VITE_API_BASE_URL': JSON.stringify('/moshu/api/v1'),
  },
  build: {
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          if (id.includes('naive-ui')) return 'naive-ui'
          if (id.includes('echarts') || id.includes('zrender')) return 'echarts'
          if (id.includes('@vue')) return 'vue-runtime'
          return 'vendor'
        },
      },
    },
  },
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    host: '127.0.0.1',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8005',
        changeOrigin: true,
        ws: true,
        timeout: 0,
        rewrite: (path) => path,
      },
    },
  },
})
