export interface ApiError {
  code: string;
  message: string;
}

export interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  error: ApiError | null;
}

export interface HealthStatus {
  status: string;
}

export interface ExecutorStatus {
  alive: boolean;
  status: string;
  active_run_id: string | null;
  last_command_run_id: string | null;
  last_heartbeat_at_utc: string | null;
  heartbeat_age_seconds: number | null;
  pending_commands: number;
  warning: string | null;
}

export interface SystemStatus {
  api: { status: string };
  executor: ExecutorStatus;
  counts: {
    runs: Record<string, number>;
    captures: Record<string, number>;
    gateways: Record<string, number>;
  };
  totals: {
    runs: number;
    captures: number;
    gateways: number;
  };
  capture_observability: {
    running_capture_ids: string[];
    completed_capture_ids: string[];
    latest_capture_id: string | null;
  };
  frontend: {
    bundle_present: boolean;
  };
}

export interface ScenarioDescriptor {
  version: number;
  scenario_name: string;
  map_name: string;
  weather: WeatherConfig;
  sync: {
    enabled: boolean;
    fixed_delta_seconds: number;
  };
  ego_vehicle: {
    blueprint: string;
    spawn_point: {
      x: number;
      y: number;
      z: number;
      roll: number;
      pitch: number;
      yaw: number;
    };
  };
  traffic: {
    enabled: boolean;
    num_vehicles: number;
    num_walkers: number;
  };
  sensors: SensorsConfig;
  termination: {
    timeout_seconds: number;
    success_condition: string;
  };
  recorder: {
    enabled: boolean;
  };
  debug?: {
    viewer_friendly?: boolean;
  };
  metadata: {
    author: string;
    tags: string[];
    description: string;
    dut_model?: string | null;
  };
}

export interface WeatherConfig {
  preset: string;
  cloudiness?: number;
  precipitation?: number;
  precipitation_deposits?: number;
  wind_intensity?: number;
  wetness?: number;
  fog_density?: number;
  sun_altitude_angle?: number;
  sun_azimuth_angle?: number;
}

export interface SensorSpec {
  id: string;
  type: string;
  x?: number;
  y?: number;
  z?: number;
  roll?: number;
  pitch?: number;
  yaw?: number;
  width?: number;
  height?: number;
  fov?: number;
  horizontal_fov?: number;
  vertical_fov?: number;
  range?: number;
  channels?: number;
  points_per_second?: number;
  rotation_frequency?: number;
  reading_frequency?: number;
  attributes?: Record<string, unknown>;
}

export interface SensorsConfig {
  enabled: boolean;
  profile_name?: string | null;
  config_yaml_path?: string | null;
  sensors: SensorSpec[];
}

export interface BuiltinScenario {
  scenario_name: string;
  display_name: string;
  description: string;
  default_map_name: string;
  descriptor_template: ScenarioDescriptor;
}

export interface ScenarioCatalogItem {
  scenario_id: string;
  scenario_name: string;
  display_name: string;
  description: string;
  default_map_name: string;
  execution_support: 'native' | 'catalog_only';
  source: {
    provider: string;
    version?: string;
    class_name?: string;
    source_file?: string;
    reference?: string;
  };
  descriptor_template: ScenarioDescriptor;
}

export interface EnvironmentPreset {
  preset_id: string;
  display_name: string;
  description: string;
  weather: WeatherConfig;
}

export interface SensorProfile {
  profile_name: string;
  display_name: string;
  description: string;
  sensors: SensorSpec[];
  raw_yaml: string;
  source_path: string;
  metadata: Record<string, unknown>;
}

export interface MapOption {
  map_name: string;
  display_name: string;
  available_variants?: string[];
  preferred_variant?: 'optimized' | 'standard';
  family_key?: string;
}

export interface EvaluationProfile {
  profile_name: string;
  display_name: string;
  description: string;
  metrics: string[];
  iou_threshold: number;
  classes: string[];
}

export interface RunMetadata {
  author?: string;
  tags?: string[];
  description?: string;
  dut_model?: string | null;
}

export interface ProjectRecord {
  project_id: string;
  name: string;
  vendor: string;
  processor: string;
  description: string;
  benchmark_focus: string[];
  target_metrics: string[];
  input_modes: string[];
  status: 'ACTIVE' | 'PILOT' | 'ARCHIVED';
  created_at_utc: string | null;
  updated_at_utc: string | null;
}

export interface BenchmarkDefinition {
  benchmark_definition_id: string;
  name: string;
  description: string;
  focus_metrics: string[];
  cadence: string;
  report_shape: string;
  project_ids: string[];
  default_evaluation_profile_name: string | null;
  created_at_utc: string | null;
  updated_at_utc: string | null;
}

export interface BenchmarkTaskScenarioMatrixEntry {
  scenario_id: string;
  scenario_name: string;
  scenario_display_name: string;
  requested_map_name: string;
  resolved_map_name: string;
  display_map_name: string;
  environment_preset_id: string;
  environment_name: string;
  sensor_profile_name: string;
}

export interface BenchmarkTaskRecord {
  benchmark_task_id: string;
  project_id: string;
  project_name: string;
  dut_model: string | null;
  benchmark_definition_id: string;
  benchmark_name: string;
  status: 'CREATED' | 'RUNNING' | 'COMPLETED' | 'PARTIAL_FAILED' | 'FAILED' | 'CANCELED';
  planned_run_count: number;
  counts_by_status: Record<string, number>;
  run_ids: string[];
  scenario_matrix: BenchmarkTaskScenarioMatrixEntry[];
  hil_config: HilConfigPayload | null;
  evaluation_profile_name: string | null;
  auto_start: boolean;
  summary: {
    counts?: {
      total_runs?: number;
      completed_runs?: number;
      failed_runs?: number;
      canceled_runs?: number;
      running_runs?: number;
    };
    metrics?: {
      fps?: number | null;
      latency_ms?: number | null;
      map?: number | null;
      power_w?: number | null;
      temperature_c?: number | null;
      frame_drop_rate?: number | null;
      pass_rate?: number | null;
      anomaly_rate?: number | null;
    };
    scenario_breakdown?: Record<string, { total_runs: number; completed: number; failed: number; canceled: number }>;
    gateway_snapshot?: Record<string, unknown>;
  };
  created_at_utc: string | null;
  updated_at_utc: string | null;
  started_at_utc: string | null;
  ended_at_utc: string | null;
}

export interface ReportRecord {
  report_id: string;
  benchmark_task_id: string;
  project_id: string;
  benchmark_definition_id: string;
  dut_model: string | null;
  title: string;
  status: 'READY' | 'FAILED';
  artifact_dir: string;
  json_path: string;
  markdown_path: string;
  summary: BenchmarkTaskRecord['summary'];
  created_at_utc: string | null;
  updated_at_utc: string | null;
}

export interface RunRecord {
  run_id: string;
  status: string;
  scenario_name: string;
  map_name: string;
  created_at_utc: string | null;
  updated_at_utc: string | null;
  started_at_utc: string | null;
  ended_at_utc: string | null;
  error_reason: string | null;
  stop_requested: boolean;
  cancel_requested: boolean;
  hil_config: {
    gateway_id?: string;
    video_source?: string;
  } | null;
  evaluation_profile: {
    profile_name?: string;
  } | null;
  artifact_dir: string;
  metadata: RunMetadata;
  weather: WeatherConfig;
  sensors: SensorsConfig;
  debug: {
    viewer_friendly?: boolean;
  };
  sim_time: number | null;
  current_tick: number | null;
  wall_elapsed_seconds: number | null;
  spawned_actors_count: number | null;
}

export interface RunEvent {
  timestamp: string;
  run_id: string;
  level: string;
  event_type: string;
  message: string;
  payload: Record<string, unknown>;
}

export interface GatewayRecord {
  gateway_id: string;
  name: string;
  status: string;
  capabilities: Record<string, unknown>;
  metrics: Record<string, unknown>;
  agent_version: string | null;
  address: string | null;
  current_run_id: string | null;
  last_heartbeat_at_utc: string | null;
  last_seen_at_utc: string | null;
  created_at_utc: string | null;
  updated_at_utc: string | null;
}

export interface CaptureRecord {
  capture_id: string;
  gateway_id: string;
  source: string;
  save_format: string;
  sample_fps: number;
  max_frames: number | null;
  save_dir: string;
  manifest_path: string;
  note: string | null;
  status: string;
  saved_frames: number;
  created_at_utc: string | null;
  updated_at_utc: string | null;
  started_at_utc: string | null;
  ended_at_utc: string | null;
  error_reason: string | null;
}

export interface CaptureFrame {
  frame_index: number;
  captured_at_utc: string | null;
  relative_path: string;
  width: number | null;
  height: number | null;
  size_bytes: number | null;
}

export interface CaptureManifest {
  capture_id: string;
  gateway_id: string;
  source: string;
  save_format: string;
  sample_fps: number;
  max_frames: number | null;
  save_dir: string;
  status: string;
  note: string | null;
  saved_frames: number;
  created_at_utc: string | null;
  started_at_utc: string | null;
  ended_at_utc: string | null;
  error_reason: string | null;
  frames: CaptureFrame[];
}

export interface HilConfigPayload {
  mode: string;
  gateway_id: string;
  video_source: string;
  dut_input_mode: string;
  result_ingest_mode: string;
}

export interface EvaluationProfilePayload {
  profile_name: string;
  metrics: string[];
  iou_threshold: number;
  classes: string[];
}

export interface CreateRunPayload {
  descriptor: ScenarioDescriptor;
  hil_config?: HilConfigPayload;
  evaluation_profile?: EvaluationProfilePayload;
}

export interface CreateBenchmarkTaskPayload {
  project_id: string;
  benchmark_definition_id: string;
  dut_model?: string;
  scenario_matrix: Array<{
    scenario_id: string;
    map_name: string;
    environment_preset_id: string;
    sensor_profile_name: string;
  }>;
  hil_config?: HilConfigPayload;
  evaluation_profile_name?: string;
  auto_start?: boolean;
}

export interface RunEnvironmentState {
  run_id: string;
  descriptor_weather: WeatherConfig;
  descriptor_debug: {
    viewer_friendly?: boolean;
  };
  runtime_control: {
    weather?: WeatherConfig;
    debug?: {
      viewer_friendly?: boolean;
    };
    updated_at_utc?: string;
  };
}

export interface CreateCapturePayload {
  gateway_id: string;
  source: string;
  save_format: string;
  sample_fps: number;
  max_frames: number;
  save_dir: string;
  note?: string;
}
