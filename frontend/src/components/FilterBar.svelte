<script lang="ts">
  import type { Filters, LogLevel } from '../types';

  const ALL_LEVELS: LogLevel[] = ['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'];
  const LEVEL_COLORS: Record<LogLevel, string> = {
    DEBUG: '#64748b',
    INFO:  '#3b82f6',
    WARN:  '#f59e0b',
    ERROR: '#ef4444',
    FATAL: '#7c3aed',
  };
  const WINDOWS = [
    { label: '1h',  value: 1 },
    { label: '6h',  value: 6 },
    { label: '24h', value: 24 },
    { label: '7d',  value: 168 },
  ];

  let {
    filters,
    services = [],
    onchange,
  }: {
    filters: Filters;
    services: string[];
    onchange: (f: Filters) => void;
  } = $props();

  function toggleLevel(level: LogLevel) {
    const cur = filters.level ?? [];
    const next = cur.includes(level) ? cur.filter((l) => l !== level) : [...cur, level];
    onchange({ ...filters, level: next });
  }

  function setService(e: Event) {
    const val = (e.target as HTMLSelectElement).value;
    onchange({ ...filters, service: val ? [val] : [] });
  }

  function setHours(h: number) {
    onchange({ ...filters, hours: h });
  }

  function setQ(e: Event) {
    onchange({ ...filters, q: (e.target as HTMLInputElement).value });
  }

  function clear() {
    onchange({ hours: 24, level: [], service: [], q: '' });
  }
</script>

<div class="bar">
  <input
    class="search"
    type="text"
    placeholder="Search messages…"
    value={filters.q}
    oninput={setQ}
  />

  <div class="levels">
    {#each ALL_LEVELS as level}
      {@const active = filters.level.includes(level)}
      <button
        class="level-btn"
        class:active
        style:--color={LEVEL_COLORS[level]}
        onclick={() => toggleLevel(level)}
      >
        {level}
      </button>
    {/each}
  </div>

  <select class="select" value={filters.service[0] ?? ''} onchange={setService}>
    <option value="">All services</option>
    {#each services as s}
      <option value={s}>{s}</option>
    {/each}
  </select>

  <div class="windows">
    {#each WINDOWS as w}
      <button
        class="window-btn"
        class:active={filters.hours === w.value}
        onclick={() => setHours(w.value)}
      >
        {w.label}
      </button>
    {/each}
  </div>

  <button class="clear-btn" onclick={clear}>Clear</button>
</div>

<style>
  .bar {
    background: #1a1d27;
    border: 1px solid #2a2d3d;
    border-radius: 10px;
    padding: 16px 20px;
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
  }

  .search {
    background: #11141e;
    border: 1px solid #2a2d3d;
    border-radius: 7px;
    color: #e2e8f0;
    padding: 7px 12px;
    font-size: 13px;
    width: 220px;
    outline: none;
  }
  .search::placeholder { color: #475569; }

  .levels { display: flex; gap: 6px; }

  .level-btn {
    font-size: 11px;
    font-weight: 600;
    padding: 5px 10px;
    border-radius: 5px;
    border: 1px solid #2a2d3d;
    background: transparent;
    color: #64748b;
    cursor: pointer;
    transition: all 0.15s;
  }
  .level-btn.active {
    border-color: var(--color);
    background: color-mix(in srgb, var(--color) 15%, transparent);
    color: var(--color);
  }

  .select {
    background: #11141e;
    border: 1px solid #2a2d3d;
    border-radius: 7px;
    color: #e2e8f0;
    padding: 7px 12px;
    font-size: 13px;
    min-width: 160px;
    outline: none;
    cursor: pointer;
  }

  .windows { display: flex; gap: 4px; }

  .window-btn {
    font-size: 12px;
    padding: 5px 10px;
    border-radius: 5px;
    border: 1px solid #2a2d3d;
    background: transparent;
    color: #64748b;
    cursor: pointer;
    transition: all 0.15s;
  }
  .window-btn.active {
    border-color: #3b82f6;
    background: #3b82f622;
    color: #3b82f6;
  }

  .clear-btn {
    margin-left: auto;
    font-size: 12px;
    padding: 5px 10px;
    border-radius: 5px;
    border: 1px solid #2a2d3d;
    background: transparent;
    color: #64748b;
    cursor: pointer;
  }
  .clear-btn:hover { color: #94a3b8; }
</style>
