/**
 * Samanvaya (समान्वय) — Main Interactive Controller
 * Global utilities: Navigation, Toast notifications, Code block copy, and Micro-interactions.
 */

document.addEventListener('DOMContentLoaded', () => {
  initCopyButtons();
  initMobileMenu();
  highlightActiveNav();
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
// AI Copilot Demo functionality
function handleChatSubmit(e) {
  e.preventDefault();
  const input = document.getElementById('copilot-input');
  const chat = document.getElementById('copilot-chat');
  if (!input.value.trim()) return;

  // Add user message
  const userMsg = document.createElement('div');
  userMsg.className = 'flex justify-end';
  userMsg.innerHTML = \<div class="max-w-[85%] p-3 bg-cyan-500/20 text-cyan-100 border border-cyan-500/30 rounded-2xl rounded-br-none">\</div>\;
  chat.appendChild(userMsg);

  const query = input.value;
  input.value = '';
  chat.scrollTop = chat.scrollHeight;

  // Simulate typing delay
  setTimeout(() => {
    const aiMsg = document.createElement('div');
    aiMsg.className = 'flex justify-start opacity-0 transition-opacity duration-300';
    aiMsg.innerHTML = \<div class="max-w-[85%] p-3 bg-space-800 text-slate-200 border border-white/10 rounded-2xl rounded-bl-none">
      I've analyzed the telemetry for "\". The anomaly detector (IsolationForest) flagged this node with 98% confidence. Would you like me to map the vector embeddings?
    </div>\;
    chat.appendChild(aiMsg);
    
    // trigger reflow for transition
    void aiMsg.offsetWidth;
    aiMsg.classList.remove('opacity-0');
    chat.scrollTop = chat.scrollHeight;
  }, 1000);
}

// Vector Search Demo functionality
function handleSearchSubmit(e) {
  e.preventDefault();
  const input = document.getElementById('vector-search-input');
  const results = document.getElementById('vector-search-results');
  if (!input.value.trim()) return;

  results.innerHTML = \
    <div class="h-full flex flex-col items-center justify-center space-y-4 text-emerald-400/70">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-400"></div>
      <p class="text-sm animate-pulse">Querying vector database...</p>
    </div>
  \;

  setTimeout(() => {
    results.innerHTML = \
      <div class="space-y-3">
        <div class="p-3 bg-space-800 border border-white/10 rounded-lg cursor-pointer hover:border-emerald-500/50 transition-colors flex justify-between items-center group">
          <span class="text-sm font-medium text-slate-200 group-hover:text-emerald-300 transition-colors">\ [Tile_001_A]</span>
          <span class="text-xs bg-emerald-500/20 text-emerald-300 px-2 py-1 rounded-md border border-emerald-500/20">99% match</span>
        </div>
        <div class="p-3 bg-space-800 border border-white/10 rounded-lg cursor-pointer hover:border-emerald-500/50 transition-colors flex justify-between items-center group">
          <span class="text-sm font-medium text-slate-200 group-hover:text-emerald-300 transition-colors">Shadow crater cluster</span>
          <span class="text-xs bg-emerald-500/20 text-emerald-300 px-2 py-1 rounded-md border border-emerald-500/20">94% match</span>
        </div>
        <div class="p-3 bg-space-800 border border-white/10 rounded-lg cursor-pointer hover:border-emerald-500/50 transition-colors flex justify-between items-center group">
          <span class="text-sm font-medium text-slate-200 group-hover:text-emerald-300 transition-colors">Lunar mare topology matching</span>
          <span class="text-xs bg-emerald-500/20 text-emerald-300 px-2 py-1 rounded-md border border-emerald-500/20">87% match</span>
        </div>
      </div>
    \;
  }, 1200);
}
