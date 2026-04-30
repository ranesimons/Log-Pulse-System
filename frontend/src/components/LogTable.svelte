<script lang="ts">
  import { format, parseISO } from 'date-fns';
  import type { LogRecord } from '../types';

  const LEVEL_COLORS: Record<string, string> = {
    DEBUG: '#64748b',
    INFO:  '#3b82f6',
    WARN:  '#f59e0b',
    ERROR: '#ef4444',
    FATAL: '#7c3aed',
  };

  let {
    logs = [],
    hasMore = false,
    loading = false,
    onLoadMore,
  }: {
    logs: LogRecord[];
    hasMore: boolean;
    loading: boolean;
    onLoadMore: () => void;
  } = $props();

  let openRows = $state<string[]>([]);

  function toggle(id: string) {
    openRows = openRows.includes(id)
      ? openRows.filter((r) => r !== id)
      : [...openRows, id];
  }

  function ts(raw: string) {
    return format(parseISO(raw), 'MMM dd HH:mm:ss');
  }
</script>

<div class="table-wrap">
  <div class="scroll">
    <table>
      <thead>
        <tr>
          <th>Time</th>
          <th>Level</th>
          <th>Service</th>
          <th>Message</th>
          <th>Host</th>
        </tr>
      </thead>
      <tbody>
        {#each logs as log (log.id)}
          {@const open = openRows.includes(log.id)}
          {@const color = LEVEL_COLORS[log.level] ?? '#64748b'}
          <tr class="data-row" onclick={() => toggle(log.id)}>
            <td class="cell-time">{ts(log.timestamp)}</td>
            <td>
              <span class="badge" style:--color={color}>{log.level}</span>
            </td>
            <td class="cell-service">{log.service}</td>
            <td class="cell-message">{log.message}</td>
            <td class="cell-dim">{log.host ?? '—'}</td>
          </tr>
          {#if open}
            <tr class="detail-row">
              <td colspan={5}>
                <div class="detail-grid">
                  <span><b>ID:</b> {log.id}</span>
                  <span><b>Environment:</b> {log.environment}</span>
                  {#if log.trace_id}<span><b>Trace:</b> {log.trace_id}</span>{/if}
                  {#if log.span_id}<span><b>Span:</b> {log.span_id}</span>{/if}
                </div>
                {#if Object.keys(log.metadata).length}
                  <pre class="meta">{JSON.stringify(log.metadata, null, 2)}</pre>
                {/if}
              </td>
            </tr>
          {/if}
        {:else}
          {#if !loading}
            <tr>
              <td colspan={5} class="empty">No logs found</td>
            </tr>
          {/if}
        {/each}
      </tbody>
    </table>
  </div>

  {#if hasMore}
    <div class="load-more">
      <button disabled={loading} onclick={onLoadMore}>
        {loading ? 'Loading…' : 'Load more'}
      </button>
    </div>
  {/if}
</div>

<style>
  .table-wrap {
    background: #1a1d27;
    border: 1px solid #2a2d3d;
    border-radius: 10px;
    overflow: hidden;
  }
  .scroll { overflow-x: auto; }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  thead { background: #11141e; }

  th {
    padding: 10px 14px;
    font-size: 11px;
    font-weight: 600;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    text-align: left;
    border-bottom: 1px solid #2a2d3d;
    white-space: nowrap;
  }

  .data-row {
    cursor: pointer;
    border-bottom: 1px solid #1e2235;
    transition: background 0.1s;
  }
  .data-row:hover { background: #1e2235; }

  td { padding: 10px 14px; }

  .cell-time { font-size: 12px; color: #475569; white-space: nowrap; }
  .cell-service { font-size: 12px; color: #94a3b8; }
  .cell-message {
    font-size: 13px;
    color: #e2e8f0;
    max-width: 520px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .cell-dim { font-size: 12px; color: #475569; }

  .badge {
    font-size: 10px;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 4px;
    border: 1px solid var(--color);
    color: var(--color);
    background: color-mix(in srgb, var(--color) 12%, transparent);
    letter-spacing: 0.5px;
  }

  .detail-row {
    background: #11141e;
    border-bottom: 1px solid #1e2235;
  }
  .detail-row td { padding: 14px 20px; }

  .detail-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    font-size: 12px;
    color: #94a3b8;
    margin-bottom: 8px;
  }
  .detail-grid b { color: #64748b; }

  .meta {
    background: #0f1117;
    border-radius: 6px;
    padding: 12px;
    font-size: 11px;
    color: #64748b;
    overflow: auto;
    max-height: 180px;
  }

  .empty {
    padding: 40px;
    text-align: center;
    color: #475569;
    font-size: 13px;
  }

  .load-more {
    padding: 16px;
    text-align: center;
  }
  .load-more button {
    font-size: 13px;
    padding: 8px 24px;
    border-radius: 7px;
    border: 1px solid #2a2d3d;
    background: transparent;
    color: #94a3b8;
    cursor: pointer;
  }
  .load-more button:disabled { color: #475569; cursor: default; }
</style>
