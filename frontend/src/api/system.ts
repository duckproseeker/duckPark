import { apiRequest } from './client';
import type { SystemStatus } from './types';

export function getSystemStatus() {
  return apiRequest<SystemStatus>('/system/status');
}
