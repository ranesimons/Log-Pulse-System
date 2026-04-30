<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { api } from './api/client';
  import type { Filters, LevelBucket, LogRecord, OverviewStats, ServiceBucket, TimelineBucket } from './types';
  import FilterBar from './components/FilterBar.svelte';
  import LevelChart from './components/LevelChart.svelte';
  import LogTable from './components/LogTable.svelte';
  import ServiceChart from './components/ServiceChart.svelte';
  import StatCard from './components/StatCard.svelte';
  import TimelineChart from './components/TimelineChart.svelte';

  const POLL_MS = 15_000;

  let filters = $state<Filters>({ hours: 24, level: [], service: [], q: '' });

  let overview   = $state<OverviewStats | null>(null);
  let levelData  = $state<LevelBucket[]>([]);
  let serviceData = $state<ServiceBucket[]>([]);
  let timeline   = $state<TimelineBucket[]>([]);
  let services   = $state<string[]>([]);

  let logs       = $state<LogRecord[]>([]);
  let cursor     = $state<string | null>(null);
  let hasMore    = $state(false);
  let logsLoading = $state(false);

  async function fetchStats() {
    const h = filters.hours;
    const buckets = h <= 6 ? h * 6 : 24;
    [overview, levelData, serviceData, timeline] = await Promise.all([
      api.overview(h),
      api.byLevel(h),
      api.byService(h),
      api.timeline(h, buckets),
    ]);
  }

  async function fetchLogs(replace = true, cur: string | null = null) {
    logsLoading = true;
    try {
      const page = await api.logs({
        hours:   filters.hours,
        level:   filters.level,
        service: filters.service,
        q:       filters.q,
        limit:   50,
        cursor:  cur,
      });
      logs    = replace ? page.items : [...logs, ...page.items];
      cursor  = page.next_cursor;
      hasMore = !!page.next_cursor;
    } finally {
      logsLoading = false;
    }
  }

  function handleFiltersChange(next: Filters) {
    filters = next;
  }

  // Re-fetch whenever filters change
  $effect(() => {
    const _ = filters; // track
    fetchStats();
    fetchLogs(true, null);
  });

  let pollInterval: ReturnType<typeof setInterval>;

  onMount(async () => {
    services = await api.services();
    pollInterval = setInterval(() => {
      fetchStats();
      fetchLogs(true, null);
    }, POLL_MS);
  });

  onDestroy(() => clearInterval(pollInterval));
</script>

<div class="app">
  <!-- Header -->
  <header>
    <div class="brand">
      <div class="logo">⚡</div>
      <div>
        <div class="brand-name">Log Pulse</div>
        <div class="brand-sub">Observability Dashboard</div>
      </div>
    </div>
    <div class="live">
      <span class="dot"></span>
      Live · refreshes every {POLL_MS / 1000}s
    </div>
  </header>

  <main>
    <!-- Stat cards -->
    <div class="stats-row">
      <StatCard
        label="Total Logs ({filters.hours}h)"
        value={overview?.total_logs.toLocaleString()}
        accent="blue"
      />
      <StatCard
        label="Errors"
        value={overview?.error_count.toLocaleString()}
        sub="+ {overview?.fatal_count ?? 0} fatal"
        accent="red"
      />
      <StatCard
        label="Warnings"
        value={overview?.warn_count.toLocaleString()}
        accent="yellow"
      />
      <StatCard
        label="Error Rate"
        value={overview ? `${overview.error_rate}%` : null}
        accent={(overview?.error_rate ?? 0) > 10 ? 'red' : 'green'}
      />
      <StatCard
        label="Services"
        value={overview?.unique_services}
        accent="purple"
      />
    </div>

    <!-- Charts -->
    <div class="charts-row">
      <TimelineChart data={timeline} />
      <LevelChart data={levelData} />
      <ServiceChart data={serviceData} />
    </div>

    <!-- Filters + table -->
    <FilterBar {filters} {services} onchange={handleFiltersChange} />
    <LogTable
      {logs}
      {hasMore}
      loading={logsLoading}
      onLoadMore={() => fetchLogs(false, cursor)}
    />
  </main>
</div>

<style>
  :global(*, *::before, *::after) {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }
  :global(body) {
    font-family: 'Inter', system-ui, sans-serif;
    background: #0f1117;
    color: #e2e8f0;
  }

  .app { min-height: 100vh; }

  header {
    background: #11141e;
    border-bottom: 1px solid #1e2235;
    padding: 16px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .brand { display: flex; align-items: center; gap: 12px; }

  .logo {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: linear-gradient(135deg, #3b82f6, #7c3aed);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
  }

  .brand-name { font-size: 16px; font-weight: 700; color: #f1f5f9; }
  .brand-sub  { font-size: 11px; color: #475569; }

  .live {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: #22c55e;
  }

  .dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #22c55e;
    display: inline-block;
  }

  main {
    padding: 24px 28px 40px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .stats-row {
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
  }

  .charts-row {
    display: grid;
    grid-template-columns: 1fr 260px 340px;
    gap: 16px;
  }

  @media (max-width: 1100px) {
    .charts-row { grid-template-columns: 1fr 1fr; }
  }
  @media (max-width: 700px) {
    .charts-row { grid-template-columns: 1fr; }
  }
</style>
