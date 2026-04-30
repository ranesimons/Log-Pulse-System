<script lang="ts">
  import { onMount } from 'svelte';
  import { Chart } from 'chart.js/auto';
  import type { LevelBucket } from '../types';

  let { data = [] }: { data: LevelBucket[] } = $props();

  let canvas: HTMLCanvasElement;
  let chart: Chart | null = null;

  const COLORS: Record<string, string> = {
    DEBUG: '#64748b',
    INFO:  '#3b82f6',
    WARN:  '#f59e0b',
    ERROR: '#ef4444',
    FATAL: '#7c3aed',
  };

  function buildData(rows: LevelBucket[]) {
    return {
      labels: rows.map((r) => r.level),
      datasets: [{
        data: rows.map((r) => r.count),
        backgroundColor: rows.map((r) => COLORS[r.level] ?? '#64748b'),
        borderWidth: 0,
        hoverOffset: 4,
      }],
    };
  }

  onMount(() => {
    chart = new Chart(canvas, {
      type: 'doughnut',
      data: buildData(data),
      options: {
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
          legend: { position: 'bottom', labels: { color: '#64748b', boxWidth: 12, font: { size: 11 } } },
          tooltip: {
            backgroundColor: '#0f1117',
            borderColor: '#2a2d3d',
            borderWidth: 1,
            bodyColor: '#e2e8f0',
          },
        },
      },
    });
    return () => chart?.destroy();
  });

  $effect(() => {
    if (!chart) return;
    chart.data = buildData(data);
    chart.update('none');
  });
</script>

<div class="card">
  <p class="title">By Level</p>
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
    margin: 0 0 8px;
  }
  .chart-wrap {
    height: 200px;
    position: relative;
  }
</style>
