<script lang="ts">
  import { onMount } from 'svelte';
  import { Chart } from 'chart.js/auto';
  import type { ServiceBucket } from '../types';

  let { data = [] }: { data: ServiceBucket[] } = $props();

  let canvas: HTMLCanvasElement;
  let chart: Chart | null = null;

  function buildData(rows: ServiceBucket[]) {
    return {
      labels: rows.map((r) => r.service),
      datasets: [
        {
          label: 'Total',
          data: rows.map((r) => r.count),
          backgroundColor: '#3b82f644',
          borderColor: '#3b82f6',
          borderWidth: 1,
          borderRadius: 4,
        },
        {
          label: 'Errors',
          data: rows.map((r) => r.error_count),
          backgroundColor: '#ef444444',
          borderColor: '#ef4444',
          borderWidth: 1,
          borderRadius: 4,
        },
      ],
    };
  }

  onMount(() => {
    chart = new Chart(canvas, {
      type: 'bar',
      data: buildData(data),
      options: {
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
          legend: { labels: { color: '#64748b', boxWidth: 12, font: { size: 11 } } },
          tooltip: {
            backgroundColor: '#0f1117',
            borderColor: '#2a2d3d',
            borderWidth: 1,
            bodyColor: '#e2e8f0',
          },
        },
        scales: {
          x: { ticks: { color: '#475569', font: { size: 11 } }, grid: { color: '#1e2235' } },
          y: { ticks: { color: '#94a3b8', font: { size: 11 } }, grid: { display: false } },
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
  <p class="title">Top Services</p>
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
