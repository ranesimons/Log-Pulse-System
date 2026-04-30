import type {
  Filters,
  LevelBucket,
  LogPage,
  OverviewStats,
  ServiceBucket,
  TimelineBucket,
} from '../types';

const BASE = import.meta.env.VITE_API_URL ?? '';

async function get<T>(path: string, params: Record<string, unknown> = {}): Promise<T> {
  const url = new URL(BASE + path, window.location.origin);
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === '') continue;
    if (Array.isArray(v)) v.forEach((val) => url.searchParams.append(k, String(val)));
    else url.searchParams.set(k, String(v));
  }
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const api = {
  overview: (hours: number) =>
    get<OverviewStats>('/api/v1/stats/overview', { hours }),

  byLevel: (hours: number) =>
    get<LevelBucket[]>('/api/v1/stats/by-level', { hours }),

  byService: (hours: number, top = 10) =>
    get<ServiceBucket[]>('/api/v1/stats/by-service', { hours, top }),

  timeline: (hours: number, buckets: number) =>
    get<TimelineBucket[]>('/api/v1/stats/timeline', { hours, buckets }),

  services: () =>
    get<string[]>('/api/v1/stats/services'),

  logs: (params: Partial<Filters> & { limit?: number; cursor?: string | null }) =>
    get<LogPage>('/api/v1/logs', {
      limit: params.limit ?? 50,
      cursor: params.cursor ?? undefined,
      q: params.q || undefined,
      level: params.level?.length ? params.level : undefined,
      service: params.service?.length ? params.service : undefined,
    }),
};
