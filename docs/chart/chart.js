const O = '#f97316', B = '#3b82f6';
const OT = 'rgba(249,115,22,0.2)', BT = 'rgba(59,130,246,0.2)';
const GRID = 'rgba(255,255,255,0.06)', TK = '#64748b';
const PROMPTS = ['P1 · Estruturado', 'P2 · Texto Livre', 'P3 · Com Ruído'];

const base = () => ({
  responsive: true, maintainAspectRatio: true,
  plugins: {
    legend: { labels: { color: '#94a3b8', font: { size: 11 }, boxWidth: 10 } },
    tooltip: { backgroundColor: '#1e2535', titleColor: '#e2e8f0', bodyColor: '#94a3b8', borderColor: '#2d3748', borderWidth: 1 }
  },
  scales: {
    x: { ticks: { color: TK, font: { size: 11 } }, grid: { color: GRID } },
    y: { ticks: { color: TK, font: { size: 11 } }, grid: { color: GRID } }
  }
});

const bar = (id, baseline, multi, yPct) => new Chart(document.getElementById(id), {
  type: 'bar',
  data: {
    labels: PROMPTS,
    datasets: [
      { label: 'One-Shot', data: baseline, backgroundColor: OT, borderColor: O, borderWidth: 2, borderRadius: 6 },
      { label: 'Multiagente', data: multi,   backgroundColor: BT, borderColor: B, borderWidth: 2, borderRadius: 6 }
    ]
  },
  options: {
    ...base(),
    scales: {
      x: base().scales.x,
      y: { ...base().scales.y, ticks: { color: TK, callback: v => yPct ? v + '%' : v } }
    }
  }
});

// Cobertura (one-shot only)
new Chart(document.getElementById('coverageChart'), {
  type: 'bar',
  data: {
    labels: PROMPTS,
    datasets: [{
      label: 'Cobertura (%)',
      data: [17.6, 11.8, 26],
      backgroundColor: [OT, OT, 'rgba(251,191,36,0.2)'],
      borderColor: [O, O, '#fbbf24'],
      borderWidth: 2, borderRadius: 6
    }]
  },
  options: {
    ...base(),
    plugins: { ...base().plugins, legend: { display: false } },
    scales: {
      x: base().scales.x,
      y: { ...base().scales.y, max: 100, ticks: { color: TK, callback: v => v + '%' } }
    }
  }
});

bar('tasksChart',   [4, 8, 5], [7, 8, 9]);
bar('lanesChart',   [0, 0, 0], [5, 4, 2]);
bar('flowsChart',   [5, 16, 8], [7, 11, 9]);
bar('gatewaysChart',[1, 3, 2], [2, 1, 1]);

// Radar
new Chart(document.getElementById('radarChart'), {
  type: 'radar',
  data: {
    labels: ['Tasks', 'Gateways', 'Eventos', 'Seq. Flows', 'Lanes'],
    datasets: [
      { label: 'One-Shot',    data: [5.67, 2.0, 3.67, 9.67, 0],    backgroundColor: OT, borderColor: O, borderWidth: 2, pointBackgroundColor: O },
      { label: 'Multiagente', data: [8.0,  1.33, 3.0, 9.0, 3.67], backgroundColor: BT, borderColor: B, borderWidth: 2, pointBackgroundColor: B }
    ]
  },
  options: {
    responsive: true, maintainAspectRatio: true,
    plugins: {
      legend: { labels: { color: '#94a3b8', font: { size: 11 }, boxWidth: 10 } },
      tooltip: { backgroundColor: '#1e2535', titleColor: '#e2e8f0', bodyColor: '#94a3b8' }
    },
    scales: {
      r: {
        grid: { color: GRID },
        ticks: { color: TK, backdropColor: 'transparent', font: { size: 9 } },
        pointLabels: { color: '#94a3b8', font: { size: 11 } }
      }
    }
  }
});