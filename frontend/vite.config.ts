import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  const backendTarget = env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
  const apiProxyPaths = [
    '/healthz',
    '/runs',
    '/gateways',
    '/captures',
    '/system',
    '/scenarios',
    '/maps',
    '/evaluation-profiles',
    '/projects',
    '/benchmark-definitions',
    '/benchmark-tasks',
    '/reports'
  ];
  const httpProxyEntries = apiProxyPaths.reduce<Record<string, string>>((accumulator, path) => {
    accumulator[path] = backendTarget;
    return accumulator;
  }, {});

  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: {
        ...httpProxyEntries,
        '/ws': {
          target: backendTarget,
          ws: true
        }
      }
    },
    preview: {
      host: '0.0.0.0',
      port: 4173
    }
  };
});
