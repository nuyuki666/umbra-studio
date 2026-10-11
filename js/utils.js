/* ==========================================================================
   Umbra Studio — Utilities & Data Store
   ========================================================================== */

/**
 * DOM query selector helpers
 */
const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];

/**
 * Safe LocalStorage abstraction with in-memory fallback
 */
const mem = {};
const db = {
  get(key, defaultValue) {
    try {
      const val = localStorage.getItem(key);
      return val ? JSON.parse(val) : defaultValue;
    } catch (e) {
      return key in mem ? mem[key] : defaultValue;
    }
  },
  set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      mem[key] = value;
    }
  }
};

/**
 * HTML special characters escaper for safe rendering
 */
const esc = str =>
  String(str).replace(/[&<>"']/g, char => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[char]));

/**
 * Toast notifications
 */
function toast(message) {
  const el = $('#toast');
  if (!el) return;
  el.textContent = message;
  el.classList.add('on');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => el.classList.remove('on'), 2800);
}

/**
 * Russian Ruble currency formatter
 */
const fmt = num => (+num).toLocaleString('ru-RU') + ' ₽';

/**
 * Cryptographic SHA-256 hash helper with fallback
 */
async function hash(str) {
  try {
    const buffer = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('umbra:' + str));
    return [...new Uint8Array(buffer)].map(byte => byte.toString(16).padStart(2, '0')).join('');
  } catch (e) {
    return btoa(unescape(encodeURIComponent(str)));
  }
}

/**
 * App Configuration State
 */
const cfg = Object.assign(
  {
    open: true,
    msg: '',
    banner: '',
    minP: 5000,
    plans: {
      'Лендинг': 1500,
      'Многостраничный сайт': 3000,
      'Интернет-магазин': 5000
    },
    works: [],
    adm: null
  },
  db.get('cfg', {})
);

// Ensure default plans versioning
if (cfg.v !== 3) {
  cfg.plans = {
    'Лендинг': 1500,
    'Многостраничный сайт': 3000,
    'Интернет-магазин': 5000
  };
  cfg.v = 3;
  db.set('cfg', cfg);
}

const saveCfg = () => db.set('cfg', cfg);
const getOrders = () => db.get('orders', []);
const getUsers = () => {
  const users = db.get('u_users', {});
  // Purge any temporary demo/test accounts if present in local storage
  let changed = false;
  if (users['elyww']) {
    delete users['elyww'];
    changed = true;
  }
  if (users['elyww@umbra.studio']) {
    delete users['elyww@umbra.studio'];
    changed = true;
  }
  if (changed) {
    db.set('u_users', users);
  }
  return users;
};

