import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  server: {
    port: 3000,
    proxy: {
      '/api': { target: 'http://backend:8000', changeOrigin: true },
      '/health': { target: 'http://backend:8000', changeOrigin: true },
    },
  },
});
