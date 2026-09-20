export type Entity = {
  id: string;
  kind: string;
  label: string;
  data: {
    unit?: string;
    source?: string;
    property_type?: string;
    space_use?: string;
    occupied?: boolean;
  };
};
export type Edge = { source: string; relation: string; target: string };
export type Observation = {
  event_id: string;
  point_id: string;
  device_timestamp: string;
  value: number | null;
  source?: { file?: string };
  unit: string;
  quality: string;
  received_at?: string;
};
export type Logic = {
  operating_point: string;
  operating_equals: number;
  left: string;
  right: string;
  operator: string;
  threshold: number;
  unit: string;
  duration_minutes: number;
  freshness_seconds: number;
  severity: string;
  recovery: string;
};
export type Config = {
  name: string;
  intent: string;
  target: {
    property_type: string;
    building_ids: string[];
    floor_ids: string[];
    zone_ids: string[];
    room_ids: string[];
    equipment_type: string;
    space_use: string;
    exclude_equipment_ids: string[];
  };
  logic: Logic;
  overrides: Record<string, { threshold?: number; duration_minutes?: number }>;
};
export type Rule = {
  id: string;
  rule_id: string;
  version: number;
  status: string;
  config: Config;
  created_at: string;
};
export type Affected = {
  zones: Entity[];
  rooms: Entity[];
  installation: Entity[];
  label: string;
};
export type Sample = {
  at: string;
  observations: Record<string, Observation>;
  difference: number;
};
export type Issue = {
  id: string;
  equipment_id: string;
  version_id: string;
  status: string;
  data: {
    rule_id: string;
    rule_version: number;
    config: Config;
    effective: Logic;
    threshold: number;
    severity: string;
    triggered_at: string;
    recovered_at: string | null;
    trigger_interval: { start: string; end: string };
    observations: Sample[];
    calculated_difference: number;
    affected: Affected;
    data_quality: string;
  };
};
export type Match = {
  equipment_id: string;
  label: string;
  points: Record<string, string>;
  paths: { building: string; floor: string; zone: string; rooms: string[] }[];
  effective: Logic;
  global: Logic;
  override: { threshold?: number; duration_minutes?: number };
  affected: Affected;
};
export type Preview = {
  matches: Match[];
  exclusions: {
    equipment_id: string;
    reason: string;
    missing_points?: string[];
  }[];
  digest: string;
};
export type AIResult = {
  id: string;
  state: string;
  message?: string;
  draft?: Rule;
  preview?: Preview;
  traces: { tool: string; elapsed_ms: number }[];
};
export type Pipeline = {
  ingestion?: {
    status: string;
    heartbeat_at?: string;
    last_received_at?: string;
    lag_seconds?: number;
  };
  evaluator?: { status: string; last_evaluated_at?: string };
  rejected: number;
  duplicates: number;
  pending_evaluations: number;
  late?: number;
  incomplete?: number;
  data_gap?: number;
};
export type Audit = {
  id: number;
  at: string;
  action: string;
  data: Record<string, unknown>;
};
