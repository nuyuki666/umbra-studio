/* ==========================================================================
   Umbra Studio — Admin Dashboard & Content Management
   ========================================================================== */

let isAdmin = false;
let currentAdminTab = 'ov';

/**
 * Image downscaling & compression via HTML5 Canvas
 */
const shrinkImage = file =>
  new Promise(resolve => {
    const reader = new FileReader();
    reader.onload = () => {
      const img = new Image();
      img.onload = () => {
        const scale = Math.min(1, 720 / img.width);
        const canvas = document.createElement('canvas');
        canvas.width = img.width * scale;
        canvas.height = img.height * scale;
        canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
        resolve(canvas.toDataURL('image/jpeg', 0.72));
      };
      img.onerror = () => resolve('');
      img.src = reader.result;
    };
    reader.readAsDataURL(file);
  });

/**
 * Render Admin Dashboard
 */
function renderAdmin() {
  $$('#admTabs button').forEach(btn => btn.classList.toggle('on', btn.dataset.t === currentAdminTab));

  const orders = getOrders();
  const users = getUsers();
  const countByStatus = status => orders.filter(x => x.status === status).length;
  const userEntries = Object.entries(users);
  let html = '';

  // Overview Tab
  if (currentAdminTab === 'ov') {
    html = `
      <div class="kp">
        <div><b>${orders.length}</b>заказов</div>
        <div><b>${countByStatus('Новый')}</b>новых</div>
        <div><b>${countByStatus('В работе')}</b>в работе</div>
        <div><b>${countByStatus('Готов')}</b>готово</div>
        <div><b>${userEntries.length}</b>клиентов</div>
        <div><b>${userEntries.filter(x => x[1].banned).length}</b>в бане</div>
      </div>
      <div class="card">
        <h3>Приём заказов: ${cfg.open ? 'открыт' : 'закрыт'}</h3>
        <p>Когда приём закрыт, клиенты видят сообщение и не могут отправить заявку.</p>
        <label style="margin-top:14px">Сообщение для клиентов
          <input id="cMsg" value="${esc(cfg.msg)}" placeholder="Например: возобновим приём 1 ноября">
        </label>
        <button class="btn" data-tg>${cfg.open ? 'Закрыть приём заказов' : 'Открыть приём заказов'}</button>
      </div>
    `;
  }

  // Orders Tab
  if (currentAdminTab === 'or') {
    html = orders.length
      ? orders
          .map(
            x => `
        <div class="ord">
          <b>${x.id} · ${esc(x.type)}</b> <small>${x.date} · ${esc(x.user)}</small><br>
          ${esc(x.name)} — ${esc(x.desc)}<br>
          <small>Связь: ${esc(x.con)} · Бюджет: ${esc(x.bud)}</small>
          <div class="ar">
            <select data-st="${x.id}">
              ${['Новый', 'В работе', 'Готов', 'Отклонён']
                .map(s => `<option${s === x.status ? ' selected' : ''}>${s}</option>`)
                .join('')}
            </select>
            <input type="number" data-q="${x.id}" value="${x.quote || ''}" placeholder="Наша цена, ₽">
            <button class="btn ghost" data-do="${x.id}">Удалить</button>
          </div>
        </div>
      `
          )
          .join('')
      : '<p class="note">Заказов пока нет.</p>';
  }

  // Clients Tab
  if (currentAdminTab === 'us') {
    html = userEntries.length
      ? userEntries
          .map(
            ([mail, u]) => `
        <div class="ord">
          <b>${esc(u.name)}</b> <small>${esc(mail)}</small>${
              u.banned ? ' <span class="st" style="color:var(--er)">в бане</span>' : ''
            }
          <div class="ar">
            <button class="btn ghost" data-ban="${esc(mail)}">${u.banned ? 'Разбанить' : 'Забанить'}</button>
            <button class="btn ghost" data-du="${esc(mail)}">Удалить</button>
          </div>
        </div>
      `
          )
          .join('')
      : '<p class="note">Клиентов пока нет.</p>';
  }

  // Works Tab
  if (currentAdminTab === 'wk') {
    html =
      `
      <form id="wf" class="card" style="margin-bottom:16px">
        <div class="f2">
          <label>Название<input name="t" maxlength="60"></label>
          <label>Категория<input name="k" maxlength="40" placeholder="Лендинг, магазин…"></label>
        </div>
        <label>Описание<input name="d" maxlength="160"></label>
        <label>Обложка (изображение)<input name="im" type="file" accept="image/*"></label>
        <button class="btn">Добавить работу</button>
      </form>
    ` +
      cfg.works
        .map(
          (x, i) => `
        <div class="ord">
          ${esc(x.t)} <small>${esc(x.k)}</small>
          <div class="ar">
            <button class="btn ghost" data-dw="${i}">Удалить</button>
          </div>
        </div>
      `
        )
        .join('');
  }

  // Prices Tab
  if (currentAdminTab === 'pr') {
    html = `
      <div class="card">
        <h3>Стартовые цены</h3>
        <p>Сохраняются сразу — обновляются на сайте и в ответах чата.</p>
        <div style="margin-top:14px">
          ${Object.entries(cfg.plans)
            .map(
              ([name, price]) => `
            <label>${name}, ₽
              <input type="number" data-pl="${name}" value="${price}">
            </label>
          `
            )
            .join('')}
        </div>
      </div>
    `;
  }

  // Chat Tab
  if (currentAdminTab === 'ch') {
    html = `
      <div style="display:flex;flex-direction:column;gap:8px;margin-bottom:14px">
        ${
          chatHistory
            .map(m => `<div class="m ${m.r}" style="max-width:100%">${esc(m.t)}</div>`)
            .join('') || '<p class="note">Сообщений пока нет.</p>'
        }
      </div>
      <form id="cf3" class="ar">
        <input name="m" placeholder="Ответ от оператора" autocomplete="off">
        <button class="btn">Ответить</button>
        <button type="button" class="btn ghost" data-cc>Очистить</button>
      </form>
    `;
  }

  // Settings Tab
  if (currentAdminTab === 'st') {
    html = `
      <div class="card">
        <h3>Баннер на сайте</h3>
        <p>Короткое объявление над шапкой. Пусто — баннер скрыт.</p>
        <label style="margin-top:14px">Текст
          <input id="bn" value="${esc(cfg.banner)}" maxlength="120">
        </label>
      </div>
      <div class="card" style="margin-top:14px">
        <h3>Сброс данных</h3>
        <p>Удалит заказы, клиентов, работы, чат и настройки в этом браузере.</p>
        <button class="btn ghost" data-rs style="margin-top:14px">Сбросить всё</button>
      </div>
    `;
  }

  const admBody = $('#admBody');
  if (admBody) admBody.innerHTML = html;
}

/**
 * Open Admin Modal
 */
function openAdminModal() {
  const adm = $('#adm');
  if (adm) {
    adm.showModal();
    renderAdmin();
  }
}

/**
 * Initialize Admin Panel
 */
function initAdmin() {
  const admOpenBtn = $('#admOpen');
  const alForm = $('#alF');

  const triggerAdminLogin = () => {
    if (isAdmin) return openAdminModal();
    $('#alT').textContent = cfg.adm ? 'Вход для администратора' : 'Создайте пароль администратора';
    $('#alP').value = '';
    $('#alE').textContent = '';
    const loginDialog = $('#admLogin');
    if (loginDialog) loginDialog.showModal();
  };

  if (admOpenBtn) {
    admOpenBtn.onclick = e => {
      e.preventDefault();
      triggerAdminLogin();
    };
  }

  // Secret admin shortcut: Ctrl+Shift+A or Alt+A
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey && e.shiftKey && e.code === 'KeyA') || (e.altKey && e.code === 'KeyA')) {
      e.preventDefault();
      triggerAdminLogin();
    }
  });

  // Secret triple click on footer brand opens admin
  const footerBrand = $('.footer-brand');
  let clickCount = 0;
  let clickTimer = null;
  if (footerBrand) {
    footerBrand.addEventListener('click', () => {
      clickCount++;
      clearTimeout(clickTimer);
      clickTimer = setTimeout(() => {
        clickCount = 0;
      }, 800);
      if (clickCount >= 3) {
        clickCount = 0;
        triggerAdminLogin();
      }
    });
  }

  if (alForm) {
    alForm.onsubmit = async e => {
      e.preventDefault();
      const pass = $('#alP').value;
      if (pass.length < 8) {
        return ($('#alE').textContent = 'Пароль — минимум 8 символов.');
      }

      const h = await hash('adm' + pass);
      if (!cfg.adm) {
        cfg.adm = h;
        saveCfg();
      } else if (cfg.adm !== h) {
        return ($('#alE').textContent = 'Неверный пароль.');
      }

      isAdmin = true;
      $('#admLogin').close();
      openAdminModal();
    };
  }

  const admTabs = $('#admTabs');
  if (admTabs) {
    admTabs.onclick = e => {
      const tab = e.target.dataset.t;
      if (tab) {
        currentAdminTab = tab;
        renderAdmin();
      }
    };
  }

  const admBody = $('#admBody');
  if (admBody) {
    // Admin click events
    admBody.onclick = e => {
      const btn = e.target.closest('button');
      if (!btn) return;
      const d = btn.dataset;

      // Toggle order intake
      if ('tg' in d) {
        cfg.msg = $('#cMsg').value.trim();
        cfg.open = !cfg.open;
        saveCfg();
        paintStudio();
      }

      // Delete order
      if (d.do) {
        db.set(
          'orders',
          getOrders().filter(x => x.id !== d.do)
        );
      }

      // Ban/unban user
      if (d.ban) {
        const users = getUsers();
        users[d.ban].banned = !users[d.ban].banned;
        db.set('u_users', users);
        if (currentUser === d.ban && users[d.ban].banned) {
          currentUser = null;
          db.set('u_session', null);
          renderAuth();
        }
      }

      // Delete user
      if (d.du) {
        const users = getUsers();
        delete users[d.du];
        db.set('u_users', users);
        renderAuth();
      }

      // Delete work
      if (d.dw) {
        cfg.works.splice(+d.dw, 1);
        saveCfg();
        renderWorks();
      }

      // Clear chat
      if ('cc' in d) {
        chatHistory.length = 0;
        db.set('chat', []);
        drawChatMessages();
      }

      // Reset all demo data
      if ('rs' in d) {
        if (!d.arm) {
          btn.dataset.arm = '1';
          btn.textContent = 'Нажмите ещё раз для сброса';
          return;
        }
        try {
          localStorage.clear();
        } catch (x) {}
        location.reload();
      }

      renderAdmin();
    };

    // Admin change events
    admBody.onchange = e => {
      const t = e.target;
      const d = t.dataset;
      const orders = getOrders();

      // Change order status
      if (d.st) {
        const found = orders.find(x => x.id === d.st);
        if (found) found.status = t.value;
        db.set('orders', orders);
      }

      // Change order quote price
      if (d.q) {
        const found = orders.find(x => x.id === d.q);
        if (found) found.quote = +t.value || 0;
        db.set('orders', orders);
        toast('Цена сохранена');
      }

      // Change plan price
      if (d.pl) {
        cfg.plans[d.pl] = +t.value || 0;
        saveCfg();
        paintStudio();
      }

      // Change min price
      if (t.id === 'mp') {
        cfg.minP = +t.value || 0;
        saveCfg();
        paintStudio();
      }

      // Change announcement banner
      if (t.id === 'bn') {
        cfg.banner = t.value.trim();
        saveCfg();
        paintStudio();
      }
    };

    // Admin submit events
    admBody.onsubmit = async e => {
      e.preventDefault();
      const form = e.target;

      // Add portfolio work
      if (form.id === 'wf') {
        const getVal = key => form.elements[key].value.trim();
        const file = form.elements.im.files[0];
        const gradients = [
          ['#3b3a6b', '#a9a5ff'],
          ['#2e4a57', '#7fd6e0'],
          ['#5b3a4f', '#ff9ab8'],
          ['#4a4a2e', '#e6d97a']
        ];
        const randomGrad = gradients[(Math.random() * gradients.length) | 0];

        if (!getVal('t')) {
          return toast('Укажите название работы');
        }

        cfg.works.unshift({
          t: getVal('t'),
          k: getVal('k'),
          d: getVal('d'),
          img: file ? await shrinkImage(file) : '',
          c1: randomGrad[0],
          c2: randomGrad[1]
        });

        saveCfg();
        renderWorks();
        renderAdmin();
        toast('Работа добавлена');
      }

      // Operator chat reply
      if (form.id === 'cf3') {
        const val = form.elements.m.value.trim();
        if (val) {
          sayChatMessage('b', 'Оператор: ' + val);
          renderAdmin();
        }
      }
    };
  }
}
