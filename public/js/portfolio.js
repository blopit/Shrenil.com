// Shrenil.com — portfolio interactions (vanilla, no deps)

(function () {
  'use strict';

  // ----- Sticky nav: show after hero scrolls past -----
  const nav = document.querySelector('.topnav');
  const hero = document.querySelector('.hero');
  if (nav && hero) {
    const observer = new IntersectionObserver(
      (entries) => {
        const heroEntry = entries[0];
        nav.classList.toggle('is-visible', !heroEntry.isIntersecting);
      },
      { rootMargin: '-80px 0px 0px 0px', threshold: 0 }
    );
    observer.observe(hero);
  }

  // ----- Interactive pipeline: click a stage to expand details -----
  const stages = document.querySelectorAll('.pipe-stage');
  stages.forEach((btn) => {
    btn.addEventListener('click', () => {
      const detailId = btn.getAttribute('aria-controls');
      const detail = detailId ? document.getElementById(detailId) : null;
      if (!detail) return;
      const isOpen = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', String(!isOpen));
      detail.classList.toggle('is-open', !isOpen);
    });
  });

  // ----- Role-fit selector: tabs swap panels -----
  const tablist = document.querySelector('.role-tabs');
  if (tablist) {
    const tabs = Array.from(tablist.querySelectorAll('.role-tab'));
    const panels = Array.from(document.querySelectorAll('.role-panel'));

    function activate(roleId) {
      tabs.forEach((t) => {
        const isActive = t.dataset.role === roleId;
        t.setAttribute('aria-selected', String(isActive));
        t.tabIndex = isActive ? 0 : -1;
      });
      panels.forEach((p) => {
        p.classList.toggle('is-active', p.dataset.role === roleId);
      });
    }

    tabs.forEach((tab) => {
      tab.addEventListener('click', () => activate(tab.dataset.role));
    });

    // Arrow-key navigation between tabs (WAI-ARIA pattern)
    tablist.addEventListener('keydown', (e) => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
      e.preventDefault();
      const current = tabs.findIndex((t) => t.getAttribute('aria-selected') === 'true');
      let nextIdx = current;
      if (e.key === 'ArrowLeft') nextIdx = (current - 1 + tabs.length) % tabs.length;
      if (e.key === 'ArrowRight') nextIdx = (current + 1) % tabs.length;
      if (e.key === 'Home') nextIdx = 0;
      if (e.key === 'End') nextIdx = tabs.length - 1;
      const next = tabs[nextIdx];
      activate(next.dataset.role);
      next.focus();
    });
  }

  // ----- Update copyright year -----
  const year = document.querySelector('[data-year]');
  if (year) year.textContent = String(new Date().getFullYear());
})();
