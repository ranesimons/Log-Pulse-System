<script lang="ts">
  import { onMount } from 'svelte';
  import { Chart } from 'chart.js/auto';
  import { format, parseISO } from 'date-fns';
  import type { TimelineBucket } from '../types';

  let { data = [] }: { data: TimelineBucket[] } = $props();

  let canvas: HTMLCanvasElement;
  let chart: Chart | null = null;

  const COLORS = {
    info:  '#3b82f6',
    warn:  '#f59e0b',
    error: '#ef4444',
    fatal: '#7c3aed',
    debug: '#64748b',
  };

  function buildDatasets(rows: TimelineBucket[]) {
    const labels = rows.map((r) => format(parseISO(r.bucket), 'HH:mm'));
    return {
      labels,
      datasets: (['info', 'warn', 'error', 'fatal', 'debug'] as const).map((key) => ({
        label: key.toUpperCase(),
        data: rows.map((r) => r[key]),
        borderColor: COLORS[key],
        backgroundColor: COLORS[key] + '33',
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 1.5,
      })),
    };
  }

  onMount(() => {
    chart = new Chart(canvas, {
      type: 'line',
      data: buildDatasets(data),
      options: {
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { labels: { color: '#64748b', boxWidth: 12, font: { size: 11 } } },
          tooltip: {
            backgroundColor: '#0f1117',
            borderColor: '#2a2d3d',
            borderWidth: 1,
            titleColor: '#94a3b8',
            bodyColor: '#e2e8f0',
          },
        },
        scales: {
          x: { ticks: { color: '#475569', font: { size: 11 } }, grid: { color: '#1e2235' } },
          y: { ticks: { color: '#475569', font: { size: 11 } }, grid: { color: '#1e2235' }, stacked: true },
        },
      },
    });
    return () => chart?.destroy();
  });

  $effect(() => {
    if (!chart) return;
    const next = buildDatasets(data);
    chart.data = next;
    chart.update('none');
  });
</script>

<div class="card">
  <p class="title">Log Volume Over Time</p>
  <div class="chart-wrap">
    <canvas bind:this={canvas}></canvas>
  </div>
</div>

<style>
  .card {
    background: #1a1d27;
    border: 1px solid #2a2d3d;
    border-radius: 10px;
    padding: 20px 24px;
  }
  .title {
    font-size: 13px;
    font-weight: 600;
    color: #94a3b8;
    margin: 0 0 16px;
  }
  .chart-wrap {
    height: 220px;
    position: relative;
  }
</style>
