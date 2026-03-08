import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  const backendTarget = env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: {
        '/healthz': backendTarget,
        '/runs': backendTarget,
        '/gateways': backendTarget,
        '/captures': backendTarget,
        '/system': backendTarget,
        '/scenarios': backendTarget,
        '/maps': backendTarget,
        '/evaluation-profiles': backendTarget
      }
    },
    preview: {
      host: '0.0.0.0',
      port: 4173
    }
  };
});
