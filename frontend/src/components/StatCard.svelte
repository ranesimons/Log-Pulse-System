<script lang="ts">
  const ACCENT_COLORS: Record<string, string> = {
    red:    '#ef4444',
    yellow: '#f59e0b',
    blue:   '#3b82f6',
    green:  '#22c55e',
    purple: '#a855f7',
  };

  let {
    label,
    value,
    sub,
    accent = 'blue',
  }: {
    label: string;
    value: string | number | null | undefined;
    sub?: string;
    accent?: string;
  } = $props();

  const color = $derived(ACCENT_COLORS[accent] ?? '#64748b');
</script>

<div class="card" style:border-left-color={color}>
  <span class="label">{label}</span>
  <span class="value">{value ?? '—'}</span>
  {#if sub}<span class="sub">{sub}</span>{/if}
</div>

<style>
  .card {
    background: #1a1d27;
    border: 1px solid #2a2d3d;
    border-left-width: 3px;
    border-radius: 10px;
    padding: 18px 22px;
    min-width: 160px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .label {
    font-size: 11px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  .value {
    font-size: 30px;
    font-weight: 700;
    color: #f1f5f9;
  }
  .sub {
    font-size: 12px;
    color: #64748b;
  }
</style>
