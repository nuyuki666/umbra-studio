/* ==========================================================================
   Umbra Studio — Interactive Animations & Motion Effects
   ========================================================================== */

/**
 * Procedural Starfield Generator
 */
function initStars() {
  const starsEl = $('#stars');
  if (!starsEl) return;
  const stars = [];
  for (let i = 0; i < 90; i++) {
    const x = (Math.random() * 100).toFixed(1);
    const y = (Math.random() * 100).toFixed(1);
    const size = Math.random() < 0.2 ? 1 : 0;
    const opacity = (0.15 + Math.random() * 0.5).toFixed(2);
    stars.push(`${x}vw ${y}vh 0 ${size}px rgba(255,255,255,${opacity})`);
  }
  starsEl.style.boxShadow = stars.join(',');
}

/**
 * Dynamic Typewriter in Hero Section
 */
function initTypewriter() {
  const words = ['лендинги', 'интернет-магазины', 'корпоративные сайты', 'редизайн сайтов'];
  const el = $('#typed');
  if (!el) return;

  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    el.textContent = words[0];
    return;
  }

  let wordIdx = 0;
  let charIdx = 0;
  let isDeleting = false;

  function tick() {
    const currentWord = words[wordIdx];
    el.textContent = currentWord.slice(0, charIdx);

    if (!isDeleting && charIdx === currentWord.length) {
      isDeleting = true;
      setTimeout(tick, 1400);
      return;
    }

    if (isDeleting && charIdx === 0) {
      isDeleting = false;
      wordIdx = (wordIdx + 1) % words.length;
    }

    charIdx += isDeleting ? -1 : 1;
    setTimeout(tick, isDeleting ? 35 : 70);
  }

  tick();
}

/**
 * Scroll Progress Bar, Nebula Parallax, Smart Navbar & Card Spotlight Glow
 */
let lastScrollY = 0;

function initParallaxAndScroll() {
  const progressBar = $('#bar');
  const nebula = $('.neb');
  const nav = $('.nav');

  window.addEventListener(
    'scroll',
    () => {
      const scrollY = window.scrollY;
      const doc = document.documentElement;
      const maxScroll = doc.scrollHeight - window.innerHeight || 1;

      // Reading progress bar at top of page
      if (progressBar) {
        progressBar.style.transform = `scaleX(${Math.min(1, scrollY / maxScroll)})`;
      }

      // Parallax translateY for nebula background
      if (nebula) {
        nebula.style.setProperty('--py', `${-scrollY * 0.05}px`);
      }

      // Smart navbar hiding on scroll down
      if (nav) {
        nav.classList.toggle('hide', scrollY > lastScrollY && scrollY > 240);
      }

      lastScrollY = scrollY;
    },
    { passive: true }
  );

  // Mouse spotlight glow tracking
  document.addEventListener('pointermove', e => {
    if (nebula) {
      nebula.style.setProperty('--cx', `${e.clientX}px`);
      nebula.style.setProperty('--cy', `${e.clientY}px`);
    }

    const card = e.target.closest && e.target.closest('.card');
    if (card) {
      const rect = card.getBoundingClientRect();
      card.style.setProperty('--mx', `${e.clientX - rect.left}px`);
      card.style.setProperty('--my', `${e.clientY - rect.top}px`);
    }
  });
}

/**
 * Scroll Reveal Animations (IntersectionObserver)
 */
let revealObserver;

function initScrollReveal() {
  revealObserver = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const target = entry.target;
          target.classList.add('in');
          revealObserver.unobserve(target);
          setTimeout(() => {
            target.style.transitionDelay = '';
          }, 1400);
        }
      });
    },
    { threshold: 0.1 }
  );

  // Mark all animatable cards and sections with .rv
  $$(
    '.card, .stats div, details, .steps li, .mq, section h2, section .lead, #orderForm label, footer .wrap, .hero .wrap > *'
  ).forEach(el => el.classList.add('rv'));

  observeReveal();
}

function observeReveal() {
  if (!revealObserver) return;
  $$('.rv:not(.in)').forEach((el, index) => {
    el.style.transitionDelay = `${(index % 4) * 90}ms`;
    revealObserver.observe(el);
  });
}

/**
 * Active Navigation Link Tracker
 */
function initNavObserver() {
  const sections = ['advantages', 'plans', 'works', 'order', 'faq'];
  const links = $$('.links a');

  const navObserver = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const id = entry.target.id;
          links.forEach(link => {
            link.classList.toggle('on', link.getAttribute('href') === `#${id}`);
          });
        }
      });
    },
    { rootMargin: '-45% 0px -50% 0px' }
  );

  sections.forEach(id => {
    const el = document.getElementById(id);
    if (el) navObserver.observe(el);
  });
}

/**
 * Endless Marquee Duplicator
 */
function initMarquee() {
  const marqueeInner = $('.mq div');
  if (marqueeInner) {
    marqueeInner.innerHTML += marqueeInner.innerHTML;
  }
}
