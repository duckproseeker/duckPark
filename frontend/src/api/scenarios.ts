import { apiRequest } from './client';
import type {
  BuiltinScenario,
  EnvironmentPreset,
  EvaluationProfile,
  HealthStatus,
  MapOption,
  ScenarioCatalogItem,
  SensorProfile
} from './types';

export function listScenarios() {
  return apiRequest<{
    builtins: BuiltinScenario[];
    catalog: ScenarioCatalogItem[];
    environment_presets: EnvironmentPreset[];
    sensor_profiles: SensorProfile[];
    sample_descriptors: string[];
  }>('/scenarios');
}

export function listScenarioCatalog() {
  return apiRequest<{ items: ScenarioCatalogItem[] }>('/scenarios/catalog').then((data) => data.items);
}

export function listEnvironmentPresets() {
  return apiRequest<{ items: EnvironmentPreset[] }>('/scenarios/environment-presets').then(
    (data) => data.items
  );
}

export function listSensorProfiles() {
  return apiRequest<{ items: SensorProfile[] }>('/scenarios/sensor-profiles').then((data) => data.items);
}

export function listMaps() {
  return apiRequest<{ maps: MapOption[] }>('/maps').then((data) => data.maps);
}

export function listEvaluationProfiles() {
  return apiRequest<{ profiles: EvaluationProfile[] }>('/evaluation-profiles').then(
    (data) => data.profiles
  );
}

export function getHealthStatus() {
  return apiRequest<HealthStatus>('/healthz');
}
