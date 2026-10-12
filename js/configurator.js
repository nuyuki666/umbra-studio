/* ==========================================================================
   Umbra Studio — Interactive 3D Project Configurator
   ========================================================================== */

const CONFIG_DATA = {
  types: {
    landing: { name: 'Лендинг', price: 18900, days: 5, tag: '⚡ Лендинг' },
    corporate: { name: 'Корпоративный сайт', price: 39000, days: 14, tag: '🏢 Корпоративный' },
    shop: { name: 'Интернет-магазин', price: 69000, days: 21, tag: '🛒 Интернет-магазин' },
    webapp: { name: 'Web-сервис / App', price: 55000, days: 18, tag: '📱 WebApp / Сервис' },
    redesign: { name: 'Редизайн сайта', price: 25000, days: 7, tag: '✨ Редизайн' }
  },
  styles: {
    cyber: { name: 'Dark Cyber & Glass', tag: '🌌 Cyber' },
    minimal: { name: 'Clean Minimalism', tag: '⚪ Minimal' },
    editorial: { name: 'Bold Editorial', tag: '🎨 Editorial' },
    luxury: { name: 'High-Tech Luxury', tag: '💎 Luxury' }
  },
  modules: {
    anim: { name: '3D-анимации и WebGL', price: 6000, days: 2, tag: '3D WebGL' },
    bot: { name: 'Онлайн-чат + Telegram-бот', price: 8000, days: 2, tag: 'Чат + TG' },
    pay: { name: 'Эквайринг и онлайн-оплата', price: 7000, days: 1, tag: 'Оплата' },
    sec: { name: 'Turnstile защита от спама', price: 4000, days: 0, tag: 'Turnstile' },
    cms: { name: 'Панель управления (CMS / Админка)', price: 12000, days: 3, tag: 'CMS' },
    speed: { name: 'Турбо-скорость 100/100', price: 5000, days: 1, tag: 'Скорость 100' }
  },
  speeds: {
    std: { name: 'Стандартный', mult: 1, dmult: 1 },
    fast: { name: 'Приоритет (-30% времени)', mult: 1.2, dmult: 0.7 },
    turbo: { name: 'Turbo-спринт (до 72 ч)', mult: 1.45, dmult: 0.4 }
  }
};

let activeConfig = {
  type: 'landing',
  style: 'cyber',
  modules: ['anim', 'bot', 'sec', 'speed'],
  speed: 'std',
  totalPrice: 33900,
  totalDays: 7
};

let currentAnimatedPrice = 33900;
let priceAnimTimer = null;

function animatePriceDisplay(targetVal) {
  const priceNumEl = document.getElementById('cfgPriceNum');
  if (!priceNumEl) return;

  clearInterval(priceAnimTimer);
  const startVal = currentAnimatedPrice;
  const diff = targetVal - startVal;
  const duration = 280;
  const startTime = performance.now();

  priceAnimTimer = setInterval(() => {
    const elapsed = performance.now() - startTime;
    const progress = Math.min(1, elapsed / duration);
    const ease = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(startVal + diff * ease);

    priceNumEl.textContent = new Intl.NumberFormat('ru-RU').format(current);

    if (progress >= 1) {
      clearInterval(priceAnimTimer);
      currentAnimatedPrice = targetVal;
    }
  }, 16);
}

function calculateConfig() {
  const typeObj = CONFIG_DATA.types[activeConfig.type] || CONFIG_DATA.types.landing;
  const styleObj = CONFIG_DATA.styles[activeConfig.style] || CONFIG_DATA.styles.cyber;
  const speedObj = CONFIG_DATA.speeds[activeConfig.speed] || CONFIG_DATA.speeds.std;

  let basePrice = typeObj.price;
  let baseDays = typeObj.days;

  const selectedModNames = [];
  const selectedTags = [typeObj.tag, styleObj.tag];

  activeConfig.modules.forEach(modId => {
    const mod = CONFIG_DATA.modules[modId];
    if (mod) {
      basePrice += mod.price;
      baseDays += mod.days;
      selectedModNames.push(mod.name);
      selectedTags.push(mod.tag);
    }
  });

  const finalPrice = Math.round((basePrice * speedObj.mult) / 100) * 100;
  const finalDays = Math.max(3, Math.round(baseDays * speedObj.dmult));

  activeConfig.totalPrice = finalPrice;
  activeConfig.totalDays = finalDays;

  // Animate price counter
  animatePriceDisplay(finalPrice);

  // Update days indicator
  const daysEl = document.getElementById('cfgDays');
  if (daysEl) {
    daysEl.textContent = `Срок: ~${finalDays}-${finalDays + 2} раб. дней (${speedObj.name})`;
  }

  // Update wireframe preview tags
  const wireTagsEl = document.getElementById('cfgWireTags');
  if (wireTagsEl) {
    wireTagsEl.innerHTML = selectedTags.map(t => `<span>${esc(t)}</span>`).join('');
  }

  // Update random dynamic config hash
  const codeEl = document.getElementById('cfgCode');
  if (codeEl) {
    const hash = ((finalPrice + finalDays * 31) % 9000 + 1000);
    codeEl.textContent = `CFG-${hash}`;
  }
}

function initConfigurator() {
  const section = document.getElementById('configurator');
  if (!section) return;

  // Type selection
  const typeGroup = document.getElementById('cfgTypeGroup');
  if (typeGroup) {
    typeGroup.addEventListener('click', e => {
      const btn = e.target.closest('.btn-3d');
      if (!btn || !btn.dataset.type) return;
      typeGroup.querySelectorAll('.btn-3d').forEach(b => b.classList.remove('on'));
      btn.classList.add('on');
      activeConfig.type = btn.dataset.type;
      if (window.cyberAudio) window.cyberAudio.playClick();
      calculateConfig();
    });
  }

  // Style selection
  const styleGroup = document.getElementById('cfgStyleGroup');
  if (styleGroup) {
    styleGroup.addEventListener('click', e => {
      const btn = e.target.closest('.btn-3d');
      if (!btn || !btn.dataset.style) return;
      styleGroup.querySelectorAll('.btn-3d').forEach(b => b.classList.remove('on'));
      btn.classList.add('on');
      activeConfig.style = btn.dataset.style;
      if (window.cyberAudio) window.cyberAudio.playClick();
      calculateConfig();
    });
  }

  // Modules selection (multi-select)
  const modulesGroup = document.getElementById('cfgModulesGroup');
  if (modulesGroup) {
    modulesGroup.addEventListener('click', e => {
      const btn = e.target.closest('.toggle-3d');
      if (!btn || !btn.dataset.mod) return;
      btn.classList.toggle('on');
      const modId = btn.dataset.mod;
      if (btn.classList.contains('on')) {
        if (!activeConfig.modules.includes(modId)) activeConfig.modules.push(modId);
      } else {
        activeConfig.modules = activeConfig.modules.filter(m => m !== modId);
      }
      if (window.cyberAudio) window.cyberAudio.playClick();
      calculateConfig();
    });
  }

  // Speed selection
  const speedGroup = document.getElementById('cfgSpeedGroup');
  if (speedGroup) {
    speedGroup.addEventListener('click', e => {
      const btn = e.target.closest('.btn-3d');
      if (!btn || !btn.dataset.speed) return;
      speedGroup.querySelectorAll('.btn-3d').forEach(b => b.classList.remove('on'));
      btn.classList.add('on');
      activeConfig.speed = btn.dataset.speed;
      if (window.cyberAudio) window.cyberAudio.playClick();
      calculateConfig();
    });
  }

  // Transfer configuration to order form
  const applyBtn = document.getElementById('cfgApplyBtn');
  if (applyBtn) {
    applyBtn.addEventListener('click', () => {
      const typeObj = CONFIG_DATA.types[activeConfig.type] || CONFIG_DATA.types.landing;
      const styleObj = CONFIG_DATA.styles[activeConfig.style] || CONFIG_DATA.styles.cyber;
      const speedObj = CONFIG_DATA.speeds[activeConfig.speed] || CONFIG_DATA.speeds.std;

      const modNames = activeConfig.modules
        .map(m => CONFIG_DATA.modules[m]?.name)
        .filter(Boolean)
        .join(', ');

      const briefText = `Конфигурация [${document.getElementById('cfgCode')?.textContent || 'CFG'}]:
• Тип: ${typeObj.name}
• Стиль: ${styleObj.name}
• Модули: ${modNames || 'Без доп. модулей'}
• Темп: ${speedObj.name} (~${activeConfig.totalDays} дней)
• Расчёт: ${new Intl.NumberFormat('ru-RU').format(activeConfig.totalPrice)} ₽`;

      // Set order form inputs
      const oType = document.getElementById('oType');
      if (oType) {
        if (activeConfig.type === 'shop') oType.value = 'Интернет-магазин';
        else if (activeConfig.type === 'corporate') oType.value = 'Многостраничный сайт';
        else if (activeConfig.type === 'redesign') oType.value = 'Редизайн';
        else oType.value = 'Лендинг';
      }

      const oDesc = document.getElementById('oDesc');
      if (oDesc) {
        oDesc.value = briefText;
      }

      const oBud = document.getElementById('oBud');
      const oRange = document.getElementById('oRange');
      const bVal = document.getElementById('bVal');
      if (oBud) oBud.value = activeConfig.totalPrice;
      if (oRange) oRange.value = Math.min(200000, Math.max(15000, activeConfig.totalPrice));
      if (bVal) bVal.textContent = new Intl.NumberFormat('ru-RU').format(activeConfig.totalPrice) + ' ₽';

      // Play sound & smooth scroll
      if (window.cyberAudio) window.cyberAudio.playSuccess();

      const orderSection = document.getElementById('order');
      if (orderSection) {
        orderSection.scrollIntoView({ behavior: 'smooth' });
      }

      const orderForm = document.getElementById('orderForm');
      if (orderForm) {
        orderForm.classList.remove('flash');
        void orderForm.offsetWidth;
        orderForm.classList.add('flash');
      }

      if (typeof toast === 'function') {
        toast('Конфигурация перенесена в форму заказа!');
      }
    });
  }

  // Initial calculation
  calculateConfig();
}

window.initConfigurator = initConfigurator;
