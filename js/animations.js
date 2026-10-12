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
          }, 500);
        }
      });
    },
    { threshold: 0.05, rootMargin: '0px 0px -30px 0px' }
  );

  // Mark only main cards and sections with .rv (avoid lagging inner inputs/labels)
  $$(
    '.card, .plan, .work, .stats div, details, .steps li'
  ).forEach(el => el.classList.add('rv'));

  observeReveal();
}

function observeReveal() {
  if (!revealObserver) return;
  $$('.rv:not(.in)').forEach((el, index) => {
    el.style.transitionDelay = `${(index % 3) * 35}ms`;
    revealObserver.observe(el);
  });
}

/**
 * Active Navigation Link Tracker
 */
function initNavObserver() {
  const sections = ['advantages', 'plans', 'configurator', 'works', 'order', 'faq'];
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

/**
 * 3D Card Tilt & Holographic Glare Tracking
 */
function init3DTilt() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const tiltCards = document.querySelectorAll('.tilt-3d, .plan');

  tiltCards.forEach(card => {
    let ticking = false;

    card.addEventListener('pointerenter', () => {
      card.style.transition = 'transform 0.18s cubic-bezier(0.16, 1, 0.3, 1)';
    });

    card.addEventListener('pointermove', e => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const dx = (x - rect.width / 2) / (rect.width / 2);
        const dy = (y - rect.height / 2) / (rect.height / 2);

        const rotX = -dy * 5;
        const rotY = dx * 5;

        card.style.transform = `perspective(1000px) rotateX(${rotX.toFixed(2)}deg) rotateY(${rotY.toFixed(2)}deg) translateZ(3px)`;
        card.style.setProperty('--mx', `${x}px`);
        card.style.setProperty('--my', `${y}px`);
        ticking = false;
      });
    });

    card.addEventListener('pointerleave', () => {
      card.style.transition = 'transform 0.55s cubic-bezier(0.16, 1, 0.3, 1)';
      card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0)';
      setTimeout(() => {
        card.style.transition = '';
      }, 550);
    });
  });
}

/**
 * 3D Interactive Hero Mockup View Switcher
 */
function initHeroMockupTabs() {
  const mtabs = document.querySelectorAll('.mtab');
  const views = document.querySelectorAll('.mbody-view');
  if (!mtabs.length) return;

  mtabs.forEach(btn => {
    btn.addEventListener('click', () => {
      mtabs.forEach(b => b.classList.remove('on'));
      btn.classList.add('on');
      const targetView = btn.dataset.mtab;

      views.forEach(v => {
        v.classList.toggle('on', v.classList.contains(`mview-${targetView}`));
      });

      if (window.cyberAudio) window.cyberAudio.playClick();
    });
  });
}

/**
 * Cyber Click Burst Sparks
 */
function initClickParticles() {
  document.addEventListener('click', e => {
    const target = e.target.closest('button, .btn, .btn-3d, .chip, [data-plan], .theme-dot, a.btn');
    if (!target) return;

    if (window.cyberAudio && !target.closest('#soundToggleBtn')) {
      window.cyberAudio.playClick();
    }

    const count = 7;
    const colors = ['var(--ac)', 'var(--ac2)', '#52f89a', '#54e0ff', '#ffd700'];

    for (let i = 0; i < count; i++) {
      const spark = document.createElement('span');
      spark.className = 'cyber-spark';
      const angle = (i / count) * 2 * Math.PI + (Math.random() - 0.5) * 0.4;
      const dist = 30 + Math.random() * 24;
      const tx = Math.cos(angle) * dist;
      const ty = Math.sin(angle) * dist;
      const size = 3 + Math.random() * 3;
      const color = colors[Math.floor(Math.random() * colors.length)];

      spark.style.cssText = `
        left: ${e.clientX}px;
        top: ${e.clientY}px;
        width: ${size}px;
        height: ${size}px;
        background: ${color};
        box-shadow: 0 0 8px ${color};
        --tx: ${tx}px;
        --ty: ${ty}px;
      `;
      document.body.appendChild(spark);
      setTimeout(() => spark.remove(), 420);
    }
  });
}

/**
 * Theme Accent Switcher
 */
const THEMES = {
  purple: { ac: '#a9a5ff', ac2: '#7570e6', shadow: '#5550be' },
  green: { ac: '#52f89a', ac2: '#1ab862', shadow: '#128243' },
  blue: { ac: '#54e0ff', ac2: '#1fa2d6', shadow: '#147299' },
  gold: { ac: '#ffd700', ac2: '#ff9900', shadow: '#b36b00' }
};

function applyTheme(name) {
  const theme = THEMES[name] || THEMES.purple;
  const root = document.documentElement;
  root.style.setProperty('--ac', theme.ac);
  root.style.setProperty('--ac2', theme.ac2);
  root.style.setProperty('--btn-shadow', theme.shadow);

  document.querySelectorAll('.theme-dot').forEach(dot => {
    dot.classList.toggle('on', dot.dataset.theme === name);
  });
  db.set('u_theme', name);
}

function initThemeSwitcher() {
  const savedTheme = db.get('u_theme', 'purple');
  applyTheme(savedTheme);

  document.addEventListener('click', e => {
    const dot = e.target.closest('.theme-dot');
    if (!dot || !dot.dataset.theme) return;
    applyTheme(dot.dataset.theme);
    if (window.cyberAudio) window.cyberAudio.playSuccess();
  });
}

/**
 * Cyber Web Audio Synthesizer (Native Web Audio API)
 */
const cyberAudio = {
  enabled: db.get('u_sound', true),
  ctx: null,
  init() {
    if (!this.ctx && (window.AudioContext || window.webkitAudioContext)) {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  },
  playClick() {
    if (!this.enabled) return;
    try {
      this.init();
      if (!this.ctx) return;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(1300, this.ctx.currentTime + 0.032);
      gain.gain.setValueAtTime(0.045, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.032);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.033);
    } catch (e) {}
  },
  playSuccess() {
    if (!this.enabled) return;
    try {
      this.init();
      if (!this.ctx) return;
      const notes = [523.25, 659.25, 783.99, 1046.5];
      notes.forEach((freq, idx) => {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'triangle';
        const start = this.ctx.currentTime + idx * 0.055;
        osc.frequency.setValueAtTime(freq, start);
        gain.gain.setValueAtTime(0.04, start);
        gain.gain.exponentialRampToValueAtTime(0.001, start + 0.16);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(start);
        osc.stop(start + 0.17);
      });
    } catch (e) {}
  }
};
window.cyberAudio = cyberAudio;

function initSoundToggle() {
  const btn = document.getElementById('soundToggleBtn');
  if (!btn) return;

  const updateSoundUI = () => {
    const onIcon = btn.querySelector('.sound-on-icon');
    const offIcon = btn.querySelector('.sound-off-icon');
    if (onIcon) onIcon.style.display = cyberAudio.enabled ? 'block' : 'none';
    if (offIcon) offIcon.style.display = cyberAudio.enabled ? 'none' : 'block';
    btn.classList.toggle('muted', !cyberAudio.enabled);
  };

  updateSoundUI();

  btn.addEventListener('click', () => {
    cyberAudio.enabled = !cyberAudio.enabled;
    db.set('u_sound', cyberAudio.enabled);
    updateSoundUI();
    if (cyberAudio.enabled) cyberAudio.playClick();
    if (typeof toast === 'function') {
      toast(cyberAudio.enabled ? 'Звуковые 3D эффекты включены' : 'Звук выключен');
    }
  });
}
