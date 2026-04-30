export type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'FATAL';

export interface LogRecord {
  id: string;
  timestamp: string;
  level: LogLevel;
  service: string;
  message: string;
  host: string | null;
  environment: string;
  trace_id: string | null;
  span_id: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface LogPage {
  items: LogRecord[];
  next_cursor: string | null;
  total_hint: number | null;
}

export interface OverviewStats {
  total_logs: number;
  error_count: number;
  fatal_count: number;
  warn_count: number;
  error_rate: number;
  unique_services: number;
  window_hours: number;
}

export interface LevelBucket {
  level: string;
  count: number;
}

export interface ServiceBucket {
  service: string;
  count: number;
  error_count: number;
}

export interface TimelineBucket {
  bucket: string;
  total: number;
  debug: number;
  info: number;
  warn: number;
  error: number;
  fatal: number;
}

export interface Filters {
  hours: number;
  level: LogLevel[];
  service: string[];
  q: string;
}
