/**
 * Samanvaya (समान्वय) — Main Interactive Controller
 * Global utilities: Navigation, Toast notifications, Code block copy, and Micro-interactions.
 */

document.addEventListener('DOMContentLoaded', () => {
  initCopyButtons();
  initMobileMenu();
  highlightActiveNav();
  initMLDashboard();
});

// One-Click Code / Command Copy Utility
function initCopyButtons() {
  document.querySelectorAll('[data-copy]').forEach(button => {
    button.addEventListener('click', (e) => {
      const textToCopy = button.getAttribute('data-copy');
      if (textToCopy) {
        navigator.clipboard.writeText(textToCopy).then(() => {
          showToast('Copied to clipboard! ✓');
          const originalText = button.innerHTML;
          button.classList.add('text-emerald-400');
          setTimeout(() => {
            button.classList.remove('text-emerald-400');
          }, 2000);
        });
      }
    });
  });
}

// Global Toast Notification
function showToast(message, type = 'success') {
  let toast = document.getElementById('global-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'global-toast';
    toast.className = 'fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl bg-space-850 border border-cyan-500/40 text-cyan-200 text-xs font-mono shadow-2xl transition-all duration-300 transform translate-y-10 opacity-0 flex items-center gap-2';
    document.body.appendChild(toast);
  }

  toast.innerHTML = `<span class="text-emerald-400 font-bold">✔</span> <span>${message}</span>`;
  toast.classList.remove('translate-y-10', 'opacity-0');
  toast.classList.add('translate-y-0', 'opacity-100');

  setTimeout(() => {
    toast.classList.remove('translate-y-0', 'opacity-100');
    toast.classList.add('translate-y-10', 'opacity-0');
  }, 2500);
}

// Highlight Current Page in Navigation
function highlightActiveNav() {
  const currentPath = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPath || (currentPath === '' && href === 'index.html')) {
      link.classList.add('text-cyan-400', 'font-semibold');
      link.classList.remove('text-slate-300');
    }
  });
}

// Mobile Menu Handler
function initMobileMenu() {
  const toggleBtn = document.getElementById('mobile-menu-btn');
  const menu = document.getElementById('mobile-menu');
  if (toggleBtn && menu) {
    toggleBtn.addEventListener('click', () => {
      menu.classList.toggle('hidden');
    });
  }
}

// =========================================================
// ML TELEMETRY DASHBOARD — IsolationForest Simulator
// Low-end optimized: Canvas-only chart, rAF, IntersectionObserver
// =========================================================
const ML = (() => {
  const nodes = [
    { name: 'Align 1', rmse: 0.35, anomaly: false, conf: 98 },
    { name: 'Align 2', rmse: 0.28, anomaly: false, conf: 99 },
    { name: 'Align 3', rmse: 2.50, anomaly: true,  conf: 45 },
    { name: 'Align 4', rmse: 0.41, anomaly: false, conf: 95 },
    { name: 'Align 5', rmse: 0.33, anomaly: false, conf: 97 },
    { name: 'Align 6', rmse: 0.62, anomaly: false, conf: 88 },
    { name: 'Align 7', rmse: 1.82, anomaly: true,  conf: 38 },
    { name: 'Align 8', rmse: 0.29, anomaly: false, conf: 99 },
  ];
  let alignCounter = 8;
  let pendingChart = null;
  const THRESHOLD = 0.5;

  function drawChart() {
    const canvas = document.getElementById('rmse-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const PAD = { top: 16, right: 16, bottom: 32, left: 40 };
    const cw = W - PAD.left - PAD.right;
    const ch = H - PAD.top - PAD.bottom;
    ctx.clearRect(0, 0, W, H);

    const maxRmse = Math.max(...nodes.map(n => n.rmse), 1.0);
    const step = cw / (nodes.length - 1);

    // Grid lines
    ctx.strokeStyle = 'rgba(100,116,139,0.2)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = PAD.top + ch - (i / 4) * ch;
      ctx.beginPath(); ctx.moveTo(PAD.left, y); ctx.lineTo(PAD.left + cw, y); ctx.stroke();
      ctx.fillStyle = '#64748b'; ctx.font = '10px monospace'; ctx.textAlign = 'right';
      ctx.fillText(((maxRmse * i) / 4).toFixed(2), PAD.left - 4, y + 3);
    }

    // Threshold dashed line
    const threshY = PAD.top + ch - (THRESHOLD / maxRmse) * ch;
    ctx.save(); ctx.strokeStyle = '#f59e0b'; ctx.setLineDash([4, 4]); ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(PAD.left, threshY); ctx.lineTo(PAD.left + cw, threshY); ctx.stroke();
    ctx.restore();

    // Area fill
    const grad = ctx.createLinearGradient(0, PAD.top, 0, PAD.top + ch);
    grad.addColorStop(0, 'rgba(56,189,248,0.25)'); grad.addColorStop(1, 'rgba(56,189,248,0.0)');
    ctx.beginPath();
    nodes.forEach((n, i) => {
      const x = PAD.left + i * step, y = PAD.top + ch - (n.rmse / maxRmse) * ch;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.lineTo(PAD.left + (nodes.length - 1) * step, PAD.top + ch);
    ctx.lineTo(PAD.left, PAD.top + ch); ctx.closePath();
    ctx.fillStyle = grad; ctx.fill();

    // Line
    ctx.beginPath(); ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = 2.5;
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    nodes.forEach((n, i) => {
      const x = PAD.left + i * step, y = PAD.top + ch - (n.rmse / maxRmse) * ch;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }); ctx.stroke();

    // Data points
    nodes.forEach((n, i) => {
      const x = PAD.left + i * step, y = PAD.top + ch - (n.rmse / maxRmse) * ch;
      ctx.beginPath(); ctx.arc(x, y, n.anomaly ? 6 : 4, 0, Math.PI * 2);
      ctx.fillStyle = n.anomaly ? '#f43f5e' : '#38bdf8'; ctx.fill();
      if (n.anomaly) { ctx.strokeStyle = '#fda4af'; ctx.lineWidth = 1.5; ctx.stroke(); }
    });

    // X labels
    ctx.fillStyle = '#64748b'; ctx.font = '10px monospace'; ctx.textAlign = 'center';
    nodes.forEach((n, i) => {
      ctx.fillText(n.name.replace('Align ', '#'), PAD.left + i * step, PAD.top + ch + 20);
    });
  }

  function renderNodeCards() {
    const container = document.getElementById('node-cards');
    if (!container) return;
    container.innerHTML = nodes.slice(-4).map(n => {
      const icon = n.anomaly ? '🚨' : '✅';
      const cls = n.anomaly
        ? 'bg-rose-500/10 border border-rose-500/30'
        : 'bg-emerald-500/5 border border-emerald-500/15';
      const badge = n.anomaly
        ? 'bg-rose-500/20 text-rose-300'
        : 'bg-emerald-500/20 text-emerald-300';
      const bar = n.anomaly ? 'bg-rose-400' : 'bg-emerald-400';
      const label = n.anomaly ? 'ANOMALY' : 'NORMAL';
      return `<div class="flex items-center justify-between p-3 rounded-xl ${cls} transition-all">
        <div class="flex items-center gap-3">
          <span class="text-base">${icon}</span>
          <div>
            <div class="text-xs font-semibold text-white">${n.name}</div>
            <div class="text-[10px] text-slate-400 font-mono">conf: ${n.conf}% · RMSE: ${n.rmse}px</div>
          </div>
        </div>
        <div class="flex flex-col items-end gap-1">
          <span class="text-[10px] font-mono px-2 py-0.5 rounded-full ${badge}">${label}</span>
          <div class="w-16 h-1 rounded-full bg-slate-700 overflow-hidden">
            <div class="h-full rounded-full ${bar}" style="width:${n.conf}%"></div>
          </div>
        </div>
      </div>`;
    }).join('');
  }

  function updateStats() {
    const meanRmse = (nodes.reduce((s, n) => s + n.rmse, 0) / nodes.length).toFixed(2);
    const anomalyCount = nodes.filter(n => n.anomaly).length;
    const el1 = document.getElementById('ml-stat-rmse');
    const el2 = document.getElementById('ml-stat-anomalies');
    if (el1) el1.textContent = meanRmse + ' px';
    if (el2) el2.textContent = anomalyCount + ' / ' + nodes.length;
  }

  function refresh() {
    const btn = document.getElementById('poll-btn');
    if (btn) { btn.textContent = '↻ Polling…'; btn.disabled = true; }
    setTimeout(() => {
      alignCounter++;
      const isAnomaly = Math.random() > 0.8;
      const newNode = {
        name: 'Align ' + alignCounter,
        rmse: isAnomaly ? +(Math.random() * 3 + 1.5).toFixed(2) : +(Math.random() * 0.5 + 0.1).toFixed(2),
        anomaly: isAnomaly,
        conf: isAnomaly ? Math.floor(Math.random() * 40 + 30) : Math.floor(Math.random() * 10 + 90)
      };
      nodes.shift(); nodes.push(newNode);
      updateStats(); renderNodeCards();
      if (pendingChart) cancelAnimationFrame(pendingChart);
      pendingChart = requestAnimationFrame(drawChart);
      if (btn) { btn.textContent = '↻ Poll Server'; btn.disabled = false; }
      const msg = isAnomaly ? 'Anomaly on ' + newNode.name + '! RMSE=' + newNode.rmse + 'px' : 'Telemetry nominal on ' + newNode.name;
      showToast(msg);
    }, 600);
  }

  function init() {
    if (!document.getElementById('rmse-chart')) return;
    updateStats(); renderNodeCards();
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(e => { if (e.isIntersecting) { requestAnimationFrame(drawChart); obs.disconnect(); } });
    }, { threshold: 0.1 });
    const c = document.getElementById('rmse-chart');
    if (c) obs.observe(c);
  }

  return { init, refresh };
})();

function initMLDashboard() { ML.init(); }
function refreshTelemetry() { ML.refresh(); }

// ---- Enhanced AI Copilot (ML-aware responses) ----
const COPILOT_RESPONSES = [
  function(q) { return 'IsolationForest analysis for "' + q + '": contamination score=0.08. Node Align-3 flagged (RMSE=2.50px) — solar azimuth reversal in Tycho crater. LRU cache hit-rate: 84.2%.'; },
  function(q) { return 'Vector embedding search for "' + q + '" returned 3 clusters. Top match: Tile_001_A (99.1% cosine sim, dim=768). Spatial entropy H=0.986 confirms ANMS 8x8 grid uniformity.'; },
  function(q) { return 'Pipeline telemetry for "' + q + '": mean RMSE=0.34px (threshold 0.40px ✓). Taylor Hessian refinement: O(1) analytical solve, det(H)=4ab-c²>0. MAGSAC++ inlier ratio: 94.2%.'; },
  function(q) { return 'Min-Heap severity queue for "' + q + '": top-3 critical nodes surfaced. Align-7 severity=1.82px (rank #1). Recommend re-run at sun elevation>30° to reduce crater shadow occlusion.'; },
  function(q) { return 'Polymorphic detector chain for "' + q + '": IsolationForestDetector→SlidingWindowDetector→PhaseCongruencyValidator (ABCs). All passed. Detector accuracy: 97.3%. Cache invalidated and refreshed.'; },
];
let copilotIdx = 0;

function handleChatSubmit(e) {
  e.preventDefault();
  const input = document.getElementById('copilot-input');
  const chat = document.getElementById('copilot-chat');
  if (!input || !input.value.trim()) return;

  const query = input.value.trim();
  input.value = '';

  const userMsg = document.createElement('div');
  userMsg.className = 'flex justify-end';
  userMsg.innerHTML = '<div class="max-w-[85%] p-3 bg-cyan-500/20 text-cyan-100 border border-cyan-500/30 rounded-2xl rounded-br-none text-sm">' + query + '</div>';
  chat.appendChild(userMsg);
  chat.scrollTop = chat.scrollHeight;

  const typingMsg = document.createElement('div');
  typingMsg.className = 'flex justify-start';
  typingMsg.id = 'typing-indicator';
  typingMsg.innerHTML = '<div class="p-3 bg-space-800 border border-white/10 rounded-2xl rounded-bl-none"><div class="flex gap-1 items-center"><span class="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce" style="animation-delay:0ms"></span><span class="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce" style="animation-delay:150ms"></span><span class="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce" style="animation-delay:300ms"></span></div></div>';
  chat.appendChild(typingMsg);
  chat.scrollTop = chat.scrollHeight;

  setTimeout(function() {
    var ti = document.getElementById('typing-indicator');
    if (ti) ti.remove();
    var response = COPILOT_RESPONSES[copilotIdx % COPILOT_RESPONSES.length](query);
    copilotIdx++;
    var aiMsg = document.createElement('div');
    aiMsg.className = 'flex justify-start opacity-0 transition-opacity duration-300';
    aiMsg.innerHTML = '<div class="max-w-[90%] p-3 bg-space-800 text-slate-200 border border-white/10 rounded-2xl rounded-bl-none text-xs leading-relaxed font-mono">' + response + '</div>';
    chat.appendChild(aiMsg);
    void aiMsg.offsetWidth;
    aiMsg.classList.remove('opacity-0');
    chat.scrollTop = chat.scrollHeight;
  }, 900);
}

// ---- Enhanced Vector Search ----
var SEARCH_DB = {
  'crater': [['Tycho Crater Rim Tile_001_A', 99], ['Jackson Crater Shadow Zone', 94], ['Mare Imbrium Basin', 87]],
  'shadow': [['Shadowed Crater Wall TMC2 0.25m', 98], ['Low-Sun OHRC Shadow Patch', 91], ['Crater Floor Dark Region', 83]],
  'anomaly': [['RMSE Spike Node Align_7', 99], ['IsolationForest Outlier Tile_003_B', 96], ['Solar Reversal Artifact Zone', 88]],
  'regolith': [['Lommel-Seeliger Surface Patch', 97], ['Lunar Mare Regolith Sample', 92], ['Apollo 11 Landing Site Model', 85]],
  'rmse': [['RMSE Spike Align_3 2.50px', 99], ['Sub-pixel Taylor Residual Map', 93], ['Confidence Scoring Heatmap', 86]],
};

function handleSearchSubmit(e) {
  e.preventDefault();
  var input = document.getElementById('vector-search-input');
  var results = document.getElementById('vector-search-results');
  if (!input || !input.value.trim()) return;
  var query = input.value.toLowerCase().trim();

  results.innerHTML = '<div class="h-full flex flex-col items-center justify-center space-y-3 text-emerald-400/70"><div class="animate-spin rounded-full h-6 w-6 border-b-2 border-emerald-400"></div><p class="text-xs animate-pulse font-mono">Querying 10B+ vector embeddings...</p></div>';

  setTimeout(function() {
    var hits = null;
    for (var key of Object.keys(SEARCH_DB)) {
      if (query.includes(key)) { hits = SEARCH_DB[key]; break; }
    }
    if (!hits) {
      hits = [
        [input.value + ' Lunar Tile Match', 95],
        ['Phase Congruency Map Region', 89],
        ['Fourier-Mellin Feature Cluster', 81],
      ];
    }
    results.innerHTML = '<div class="space-y-2">' + hits.map(function(h) {
      return '<div class="p-3 bg-space-800 border border-white/10 rounded-lg cursor-pointer hover:border-emerald-500/50 transition-colors flex justify-between items-center group"><div><span class="text-xs font-medium text-slate-200 group-hover:text-emerald-300 transition-colors block">' + h[0] + '</span><span class="text-[10px] text-slate-500 font-mono">cosine similarity · vector dim=768</span></div><span class="text-xs bg-emerald-500/20 text-emerald-300 px-2 py-1 rounded-md border border-emerald-500/20 shrink-0">' + h[1] + '%</span></div>';
    }).join('') + '</div>';
  }, 800);
}
