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
