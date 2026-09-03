/**
 * Samanvaya (समान्वय) — Wikipedia & Knowledge Hub Controller
 * Handles article tab switching, URL hash routing, search indexing, and FAQ accordions.
 */

document.addEventListener('DOMContentLoaded', () => {
  initWikiRouter();
  initWikiSearch();
});

// URL Hash Router for Wiki Articles
function initWikiRouter() {
  const hash = window.location.hash.replace('#', '') || 'overview';
  switchWikiArticle(hash);

  window.addEventListener('hashchange', () => {
    const currentHash = window.location.hash.replace('#', '') || 'overview';
    switchWikiArticle(currentHash);
  });
}

function switchWikiArticle(articleKey) {
  const articles = document.querySelectorAll('.wiki-article');
  let matched = false;

  articles.forEach(art => {
    if (art.id === `art-${articleKey}`) {
      art.classList.remove('hidden');
      matched = true;
    } else {
      art.classList.add('hidden');
    }
  });

  if (!matched && articles.length > 0) {
    articles[0].classList.remove('hidden');
  }

  // Update Sidebar Navigation Buttons
  document.querySelectorAll('.wiki-nav-btn').forEach(btn => {
    const target = btn.getAttribute('data-target');
    if (target === articleKey) {
      btn.className = 'wiki-nav-btn w-full text-left px-3.5 py-2.5 rounded-xl text-cyan-400 bg-cyan-950/50 border border-cyan-800/60 font-semibold flex items-center justify-between transition-all';
    } else {
      btn.className = 'wiki-nav-btn w-full text-left px-3.5 py-2.5 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-space-850 font-normal flex items-center justify-between transition-all';
    }
  });

  // Scroll to top of content container on mobile
  const contentArea = document.getElementById('wiki-content');
  if (contentArea) contentArea.scrollTop = 0;
}

// Live Search Filter for Wiki Articles & Headings
function initWikiSearch() {
  const searchInput = document.getElementById('wiki-search-input');
  if (!searchInput) return;

  searchInput.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase().trim();
    const navButtons = document.querySelectorAll('.wiki-nav-btn');

    navButtons.forEach(btn => {
      const text = btn.innerText.toLowerCase();
      const targetId = btn.getAttribute('data-target');
      const articleEl = document.getElementById(`art-${targetId}`);
      const articleContent = articleEl ? articleEl.innerText.toLowerCase() : '';

      if (text.includes(q) || articleContent.includes(q)) {
        btn.style.display = 'flex';
      } else {
        btn.style.display = 'none';
      }
    });
  });
}
