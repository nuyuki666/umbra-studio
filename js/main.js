/* ==========================================================================
   Umbra Studio — Main Application Entry Point
   ========================================================================== */

/**
 * Synchronize UI with dynamic studio state (tariffs, banner, status)
 */
function paintStudio() {
  $$('[data-p]').forEach(el => {
    el.textContent = 'от ' + fmt(cfg.plans[el.dataset.p]);
  });

  const banner = $('#banner');
  if (banner) {
    banner.hidden = !cfg.banner;
    banner.textContent = cfg.banner;
  }

  const oClosed = $('#oClosed');
  if (oClosed) {
    oClosed.hidden = cfg.open;
    oClosed.textContent = cfg.msg || 'Приём заказов временно закрыт. Загляните позже или напишите в чат.';
  }

  const orderBtn = $('#orderForm .btn');
  if (orderBtn) {
    orderBtn.disabled = !cfg.open;
  }
}

/**
 * Render portfolio grid
 */
function renderWorks() {
  const grid = $('#wGrid');
  if (!grid) return;

  const works = cfg.works;
  grid.innerHTML = works.length
    ? works
        .map(
          x => `
      <article class="card work rv">
        <div class="th" style="${
          x.img ? `background-image:url('${x.img}')` : `background:linear-gradient(135deg,${x.c1},${x.c2})`
        }"></div>
        <h3>${esc(x.t)}</h3>
        <p>${esc(x.d)}</p>
        ${x.k ? `<small>${esc(x.k)}</small>` : ''}
      </article>
    `
        )
        .join('')
    : `
      <div class="card empty rv">
        <h3>Здесь появятся наши работы</h3>
        <p>Мы только открываемся и берём первые проекты. Станьте нашим первым клиентом — ваш сайт попадёт в это портфолио.</p>
        <a class="btn" href="#order">Заказать дизайн</a>
      </div>
    `;

  observeReveal();
}

/**
 * Legal dialogs and cookie consent handlers
 */
function initLegalModals() {
  document.addEventListener('click', e => {
    const link = e.target.closest('[data-modal]');
    if (!link) return;
    e.preventDefault();
    const modalType = link.dataset.modal;
    const dialogId =
      modalType === 'privacy'
        ? '#modalPrivacy'
        : modalType === 'terms'
        ? '#modalTerms'
        : '#modalCookies';
    const dialog = $(dialogId);
    if (dialog) dialog.showModal();
  });
}

function initCookieConsent() {
  const banner = $('#cookieBanner');
  if (!banner) return;

  const isAccepted = db.get('cookies_accepted', false);
  if (!isAccepted) {
    banner.removeAttribute('hidden');
  }

  const acceptBtn = $('#acceptCookies');
  if (acceptBtn) {
    acceptBtn.addEventListener('click', () => {
      db.set('cookies_accepted', true);
      banner.setAttribute('hidden', '');
    });
  }
}

/**
 * Bootstrap on DOM ready
 */
document.addEventListener('DOMContentLoaded', () => {
  // Check banned session on startup
  const users = getUsers();
  if (currentUser && users[currentUser]?.banned) {
    currentUser = null;
    db.set('u_session', null);
  }

  // Visuals and animations
  initStars();
  initTypewriter();
  initParallaxAndScroll();
  initMarquee();

  // Content & dynamic data
  paintStudio();
  renderWorks();
  initScrollReveal();
  initNavObserver();

  // App modules
  renderAuth();
  setAuthMode('login');
  initAuth();
  initOrders();
  initChat();
  initAdmin();
  initLegalModals();
  initCookieConsent();
});

