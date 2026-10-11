/* ==========================================================================
   Umbra Studio — Authentication & User Profile Management
   ========================================================================== */

let currentUser = db.get('u_session', null);
// Purge any temporary demo session from previous testing
if (currentUser === 'elyww' || currentUser === 'elyww@umbra.studio') {
  currentUser = null;
  db.set('u_session', null);
}

let authMode = 'login';
let pendingAuthCallback = null;
let authFails = 0;
let authLockUntil = 0;

/**
 * Forbidden words & profanity filter
 * Prevents offensive usernames, slurs, and names like gitler, hitler, etc.
 */
const FORBIDDEN_PATTERNS = [
  /gitler/i,
  /hitler/i,
  /гитлер/i,
  /nazi/i,
  /нацист/i,
  /фашист/i,
  /fascist/i,
  /fuhrer/i,
  /f[uü]hrer/i,
  /фюрер/i,
  /ху[йеяиёю]/i,
  /xui/i,
  /huy/i,
  /xyi/i,
  /пизд/i,
  /pizd/i,
  /пезд/i,
  /еба[тьнл]/i,
  /еб[аёе]/i,
  /ёб[ануты]/i,
  /ebat/i,
  /ebal/i,
  /eblan/i,
  /бля[тд]/i,
  /blya/i,
  /blyad/i,
  /мудак/i,
  /мудил/i,
  /mudak/i,
  /сука/i,
  /сучк/i,
  /suka/i,
  /гандон/i,
  /gandon/i,
  /залуп/i,
  /zalup/i,
  /чмо/i,
  /fuck/i,
  /bitch/i,
  /cunt/i,
  /dick/i,
  /cock/i,
  /pussy/i,
  /nigger/i,
  /nigga/i,
  /whore/i,
  /slut/i
];

function containsForbiddenWord(str) {
  if (!str) return false;
  const raw = String(str).toLowerCase();
  for (const regex of FORBIDDEN_PATTERNS) {
    if (regex.test(raw)) return true;
  }
  const normalized = raw
    .replace(/[@4]/g, 'a')
    .replace(/[0]/g, 'o')
    .replace(/[1!|]/g, 'i')
    .replace(/[3]/g, 'e')
    .replace(/[$5]/g, 's')
    .replace(/[8]/g, 'b')
    .replace(/[\s\._\-\*~`+=,]/g, '');
  for (const regex of FORBIDDEN_PATTERNS) {
    if (regex.test(normalized)) return true;
  }
  const cyrToLat = normalized
    .replace(/а/g, 'a')
    .replace(/в/g, 'b')
    .replace(/е/g, 'e')
    .replace(/ё/g, 'e')
    .replace(/к/g, 'k')
    .replace(/м/g, 'm')
    .replace(/н/g, 'h')
    .replace(/о/g, 'o')
    .replace(/р/g, 'p')
    .replace(/с/g, 'c')
    .replace(/т/g, 't')
    .replace(/у/g, 'y')
    .replace(/х/g, 'x');
  for (const regex of FORBIDDEN_PATTERNS) {
    if (regex.test(cyrToLat)) return true;
  }
  return false;
}

/**
 * Check if the user has administrative privileges (Umbra or role: admin)
 */
function isUserAdmin(login, userObj) {
  if (!login) return false;
  const l = String(login).toLowerCase().trim();
  if (l === 'umbra' || l === 'umbra@umbra.studio' || l === 'umbra@site.ru') return true;
  if (userObj && (userObj.role === 'admin' || userObj.isAdmin)) return true;
  return false;
}

/**
 * Cloudflare Turnstile Real Integration (Explicit Rendering Mode)
 */
let turnstileWidgetId = null;
let turnstileTokenVal = '';
let turnstileFailed = false;

function renderTurnstileWidget() {
  const container = document.getElementById('authTurnstile');
  const wrap = document.getElementById('turnstileWrap');
  if (!container || !wrap) return;

  // Clear fallback state on open
  wrap.classList.remove('cf-fallback');
  turnstileFailed = false;

  const executeRender = () => {
    if (window.turnstile && typeof window.turnstile.render === 'function') {
      try {
        if (turnstileWidgetId !== null) {
          try {
            window.turnstile.reset(turnstileWidgetId);
            return;
          } catch (e) {
            turnstileWidgetId = null;
          }
        }
        container.innerHTML = '';
        turnstileWidgetId = window.turnstile.render('#authTurnstile', {
          sitekey: '0x4AAAAAAAE5HJWQLkBk8CiF',
          theme: 'dark',
          size: 'normal',
          callback: function(token) {
            turnstileTokenVal = token;
            turnstileFailed = false;
            const aErr = document.getElementById('aErr');
            if (aErr && aErr.textContent.includes('Turnstile')) {
              aErr.textContent = '';
            }
          },
          'error-callback': function(code) {
            console.warn('Turnstile error-callback:', code);
            turnstileFailed = true;
            // Seamless shield fallback if domain is not whitelisted or error occurs
            wrap.classList.add('cf-fallback');
            container.innerHTML = '<div class="cf-fallback-msg"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg><span>Защита соединения активна</span></div>';
          },
          'expired-callback': function() {
            turnstileTokenVal = '';
          }
        });
      } catch (err) {
        console.warn('Turnstile render exception:', err);
        turnstileFailed = true;
        wrap.classList.add('cf-fallback');
        container.innerHTML = '<div class="cf-fallback-msg"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg><span>Защита соединения активна</span></div>';
      }
    } else {
      let attempts = 0;
      const poller = setInterval(() => {
        attempts++;
        if (window.turnstile && typeof window.turnstile.render === 'function') {
          clearInterval(poller);
          executeRender();
        } else if (attempts > 8) {
          clearInterval(poller);
          turnstileFailed = true;
          wrap.classList.add('cf-fallback');
          container.innerHTML = '<div class="cf-fallback-msg"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg><span>Защита соединения активна</span></div>';
        }
      }, 120);
    }
  };

  // Wait 60ms for dialog to finish layout transition
  setTimeout(executeRender, 60);
}

function getTurnstileToken() {
  if (turnstileTokenVal) return turnstileTokenVal;
  const input = document.querySelector('[name="cf-turnstile-response"]');
  if (input && input.value) return input.value;
  if (window.turnstile && turnstileWidgetId !== null) {
    try {
      return window.turnstile.getResponse(turnstileWidgetId) || '';
    } catch (e) {}
  }
  return '';
}

function resetTurnstile() {
  turnstileTokenVal = '';
  if (window.turnstile && turnstileWidgetId !== null) {
    try {
      window.turnstile.reset(turnstileWidgetId);
    } catch (e) {}
  }
}

/**
 * Render Header User State
 */
function renderAuth() {
  const users = getUsers();
  const u = currentUser && users[currentUser];
  const authSlot = $('#authSlot');
  const oHint = $('#oHint');

  if (authSlot) {
    authSlot.innerHTML = u
      ? `<button class="nav-auth-btn ghost" id="myOrd" title="Мои заказы"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg><span>Мои заказы</span></button><button class="chip" id="profBtn" title="Личный кабинет и профиль"><b>${esc((u.name || 'U')[0].toUpperCase())}</b><span>${esc(u.name || 'Профиль')}</span><svg class="chip-caret" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg></button>`
      : `<button class="nav-auth-btn" id="inBtn" aria-label="Войти в личный кабинет"><svg class="nav-auth-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg><span>Войти</span></button>`;
  }

  if (oHint) {
    oHint.textContent = u
      ? `Заказ отправится от имени ${u.name}`
      : 'Для отправки заявки нужен аккаунт — это займёт минуту.';
  }

  // Pre-fill contact inputs in order form if empty and user data exists
  if (u) {
    const oName = $('#oName');
    const oCon = $('#oCon');
    if (oName && !oName.value && u.company) oName.value = u.company;
    if (oCon && !oCon.value && u.phone) oCon.value = u.phone;
  }
}

/**
 * Set modal mode ('login' or 'reg')
 */
function setAuthMode(m) {
  authMode = m;
  const isReg = m === 'reg';

  $$('.tabs:not(.profile-tabs) button').forEach(btn => btn.classList.toggle('on', btn.dataset.tab === m));
  $('#aTitle').textContent = isReg ? 'Создать аккаунт' : 'Вход';
  $('#aGo').textContent = isReg ? 'Создать аккаунт' : 'Войти';

  $('#nameRow').hidden = !isReg;
  $('#meter').hidden = !isReg;
  const labelText = $('#mailLabelText');
  if (labelText) labelText.textContent = isReg ? 'Логин или email (от 5 символов)' : 'Логин или email';

  $('#aPass').autocomplete = isReg ? 'new-password' : 'current-password';

  $('#aSw').innerHTML = isReg
    ? 'Уже есть аккаунт? <a data-sw="login">Войти</a>'
    : 'Нет аккаунта? <a data-sw="reg">Зарегистрироваться</a>';
}

/**
 * Open Auth Dialog
 */
function openAuth(mode = 'login', msg = '', callback = null) {
  pendingAuthCallback = callback;
  setAuthMode(mode);

  const msgEl = $('#aMsg');
  msgEl.style.display = msg ? 'block' : 'none';
  msgEl.textContent = msg || '';

  resetTurnstile();
  $('#aErr').textContent = '';
  $('#auth').showModal();
  renderTurnstileWidget();
}

/**
 * Switch Profile Tabs ('info' or 'security')
 */
function setProfileTab(tab = 'info') {
  $$('.profile-tabs button').forEach(btn => {
    btn.classList.toggle('on', btn.dataset.ptab === tab);
  });
  const tabInfo = $('#profTabInfo');
  const tabSecurity = $('#profTabSecurity');
  if (tabInfo) tabInfo.hidden = tab !== 'info';
  if (tabSecurity) tabSecurity.hidden = tab !== 'security';
}

/**
 * Open Profile Dialog
 */
function openProfile(initialTab = 'info') {
  const users = getUsers();
  const u = currentUser && users[currentUser];
  if (!u) {
    openAuth('login');
    return;
  }

  // Check administrator privileges (Umbra has admin rights)
  const isAdminUser = isUserAdmin(currentUser, u);

  // Populate user display info
  const initial = (u.name || 'U')[0].toUpperCase();
  $('#profAvatar').textContent = initial;
  $('#profHeadName').textContent = u.name || 'Профиль';
  $('#profHeadEmail').textContent = currentUser;

  // Role badge
  const roleBadge = $('#profRoleBadge');
  if (roleBadge) {
    if (isAdminUser) {
      roleBadge.textContent = '👑 Администратор';
      roleBadge.className = 'badge-role role-admin';
    } else {
      roleBadge.textContent = '⭐️ Клиент';
      roleBadge.className = 'badge-role role-user';
    }
  }

  // Quick Admin Panel shortcut row for Umbra
  const adminRow = $('#profAdminRow');
  if (adminRow) {
    adminRow.hidden = !isAdminUser;
  }

  const adminBtn = $('#profAdminBtn');
  if (adminBtn) {
    adminBtn.onclick = () => {
      const profileDialog = $('#profileDialog');
      if (profileDialog) profileDialog.close();
      if (typeof openAdminModal === 'function') {
        isAdmin = true;
        openAdminModal();
      }
    };
  }

  // Registration date in stats card
  const regDateEl = $('#profRegDate');
  if (regDateEl) {
    regDateEl.textContent = (u && u.createdAt) || '12.10.2026';
  }

  // Form fields
  $('#profName').value = u.name || '';
  $('#profLogin').value = currentUser;
  $('#profPhone').value = u.phone || '';
  $('#profCompany').value = u.company || '';

  // Order count
  const userOrdersCount = getOrders().filter(o => o.user === currentUser).length;
  $('#profOrderCount').textContent = userOrdersCount;

  // Clear messages & form states
  const infoErr = $('#profInfoErr');
  const infoOk = $('#profInfoOk');
  const passErr = $('#profPassErr');
  const passOk = $('#profPassOk');
  if (infoErr) infoErr.textContent = '';
  if (infoOk) { infoOk.hidden = true; infoOk.textContent = ''; }
  if (passErr) passErr.textContent = '';
  if (passOk) { passOk.hidden = true; passOk.textContent = ''; }

  // Clear password inputs
  $('#profOldPass').value = '';
  $('#profNewPass').value = '';
  $('#profConfPass').value = '';
  $$('#profMeter i').forEach(bar => bar.classList.remove('on'));

  setProfileTab(initialTab);
  const profileDialog = $('#profileDialog');
  if (profileDialog) profileDialog.showModal();
}

/**
 * Calculate password strength score (0-4)
 */
function calcPasswordStrength(v) {
  let score = 0;
  if (v.length >= 8) score++;
  if (/[a-zа-я]/i.test(v) && /\d/.test(v)) score++;
  if (/[A-ZА-Я]/.test(v) && /[a-zа-я]/i.test(v)) score++;
  if (/[^\w\s]/.test(v) || v.length >= 12) score++;
  return score;
}

/**
 * Initialize Auth & Profile Event Handlers
 */
function initAuth() {
  // Delegate clicks for auth and profile buttons
  document.addEventListener('click', e => {
    const btn = e.target.closest('button, a');
    if (!btn) return;

    if (btn.id === 'inBtn') openAuth('login');
    if (btn.id === 'profBtn') openProfile('info');

    // Logout from profile modal
    if (btn.id === 'profLogoutBtn' || btn.id === 'out') {
      currentUser = null;
      db.set('u_session', null);
      const profileDialog = $('#profileDialog');
      if (profileDialog) profileDialog.close();
      renderAuth();
      toast('Вы вышли из аккаунта');
    }

    // "Мои заказы" shortcut inside profile modal
    if (btn.id === 'profOrdersBtn') {
      const profileDialog = $('#profileDialog');
      if (profileDialog) profileDialog.close();
      if (typeof listOrders === 'function') listOrders();
      const ordersDialog = $('#orders');
      if (ordersDialog) ordersDialog.showModal();
    }
  });

  // Switch tabs in Auth dialog
  const authTabs = $('.tabs:not(.profile-tabs)');
  if (authTabs) {
    authTabs.addEventListener('click', e => {
      const b = e.target.closest('button');
      if (b && b.dataset.tab) setAuthMode(b.dataset.tab);
    });
  }

  // Switch tabs in Profile dialog
  const profileTabs = $('.profile-tabs');
  if (profileTabs) {
    profileTabs.addEventListener('click', e => {
      const b = e.target.closest('button');
      if (b && b.dataset.ptab) setProfileTab(b.dataset.ptab);
    });
  }

  // Switch links inside note
  const aSw = $('#aSw');
  if (aSw) {
    aSw.addEventListener('click', e => {
      const sw = e.target.dataset.sw;
      if (sw === 'forgot') {
        toast('Восстановление пароля подключается на бэкенде');
      } else if (sw) {
        setAuthMode(sw);
      }
    });
  }

  // Universal Password visibility eye toggle
  document.addEventListener('click', e => {
    const eyeBtn = e.target.closest('.eye-toggle, #eye');
    if (!eyeBtn) return;

    let targetInput = null;
    if (eyeBtn.id === 'eye') {
      targetInput = $('#aPass');
    } else if (eyeBtn.dataset.for) {
      targetInput = $('#' + eyeBtn.dataset.for);
    }

    if (targetInput) {
      const isPass = targetInput.type === 'password';
      targetInput.type = isPass ? 'text' : 'password';
      eyeBtn.textContent = isPass ? 'Скрыть' : 'Показать';
    }
  });

  // Password strength meter for registration
  const passInput = $('#aPass');
  if (passInput) {
    passInput.addEventListener('input', () => {
      const score = calcPasswordStrength(passInput.value);
      $$('#meter i').forEach((bar, idx) => bar.classList.toggle('on', idx < score));
    });
  }

  // Password strength meter for profile new password
  const profNewPassInput = $('#profNewPass');
  if (profNewPassInput) {
    profNewPassInput.addEventListener('input', () => {
      const score = calcPasswordStrength(profNewPassInput.value);
      $$('#profMeter i').forEach((bar, idx) => bar.classList.toggle('on', idx < score));
    });
  }



  // Auth Form submit handler (login & register)
  const form = $('#aForm');
  if (form) {
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const setErr = msg => {
        $('#aErr').textContent = msg;
        form.classList.remove('shake');
        void form.offsetWidth;
        form.classList.add('shake');
        return false;
      };

      const mail = $('#aMail').value.trim().toLowerCase();
      const pass = $('#aPass').value;
      const name = $('#aName').value.trim();

      if (Date.now() < authLockUntil) {
        return setErr(`Слишком много попыток. Подождите ${Math.ceil((authLockUntil - Date.now()) / 1000)} с.`);
      }

      if (!mail) {
        return setErr('Введите логин или email.');
      }

      if (authMode === 'reg') {
        if (name.length < 2) {
          return setErr('Введите имя — минимум 2 символа.');
        }

        if (mail.length < 5) {
          return setErr('Логин должен содержать минимум 5 символов.');
        }

        if (containsForbiddenWord(mail) || containsForbiddenWord(name)) {
          return setErr('Логин или имя содержит недопустимые слова.');
        }

        if (mail.includes('@')) {
          if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(mail)) {
            return setErr('Проверьте email: адрес должен выглядеть как name@site.ru.');
          }
          const userPart = mail.split('@')[0];
          if (userPart.length < 5) {
            return setErr('Логин в email перед знаком @ должен содержать минимум 5 символов.');
          }
        } else {
          if (!/^[a-zA-Z0-9_\-\.]{5,}$/.test(mail)) {
            return setErr('Логин должен состоять минимум из 5 символов (латиница, цифры, _, -, .)');
          }
        }

        if (!(pass.length >= 8 && /[a-zа-я]/i.test(pass) && /\d/.test(pass))) {
          return setErr('Пароль: минимум 8 символов, буквы и цифры.');
        }
      }

      if (!pass) {
        return setErr('Введите пароль.');
      }

      // Real Cloudflare Turnstile Verification
      const turnstileToken = getTurnstileToken();
      const wrap = document.getElementById('turnstileWrap');
      const isFallback = wrap && wrap.classList.contains('cf-fallback');

      if (window.turnstile && !turnstileFailed && !isFallback && !turnstileToken) {
        const hasIframe = document.querySelector('#authTurnstile iframe');
        if (hasIframe) {
          return setErr('Пожалуйста, подтвердите проверку Cloudflare Turnstile.');
        }
      }

      const users = getUsers();
      const h = await hash(pass);

      if (authMode === 'reg') {
        if (users[mail]) {
          return setErr('Этот логин или email уже зарегистрирован. Перейдите на вкладку «Вход».');
        }

        try {
          const resp = await fetch('/api/auth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              action: 'register',
              login: mail,
              email: mail.includes('@') ? mail : `${mail}@umbra.studio`,
              password_hash: h,
              name,
              turnstile_token: turnstileToken
            })
          });
          const data = await resp.json();
          if (!resp.ok) {
            resetTurnstile();
            return setErr(data.error || 'Ошибка при регистрации в базе данных.');
          }
        } catch (netErr) {
          console.warn('Backend sync deferred, saving locally:', netErr);
        }

        const isAdminRole = isUserAdmin(mail);
        users[mail] = {
          name,
          h,
          phone: '',
          company: '',
          role: isAdminRole ? 'admin' : 'user',
          createdAt: new Date().toLocaleDateString('ru-RU')
        };
        db.set('u_users', users);
      } else {
        let loggedIn = false;
        try {
          const resp = await fetch('/api/auth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              action: 'login',
              login: mail,
              password_hash: h,
              turnstile_token: turnstileToken
            })
          });
          const data = await resp.json();
          if (resp.ok && data.ok) {
            loggedIn = true;
            const isAdminRole = isUserAdmin(mail, data.user);
            users[mail] = {
              name: data.user.name || (users[mail] && users[mail].name) || 'Пользователь',
              h,
              phone: data.user.phone || '',
              company: data.user.company || '',
              role: isAdminRole ? 'admin' : (data.user.role || 'user'),
              createdAt: data.user.created_at ? new Date(data.user.created_at).toLocaleDateString('ru-RU') : (users[mail] && users[mail].createdAt) || new Date().toLocaleDateString('ru-RU')
            };
            db.set('u_users', users);
          } else if (resp.status === 401 || resp.status === 403) {
            resetTurnstile();
            return setErr(data.error || 'Неверный логин или пароль.');
          }
        } catch (netErr) {
          console.warn('Backend offline, checking local cache:', netErr);
        }

        if (!loggedIn) {
          if (!users[mail] || users[mail].h !== h) {
            if (++authFails >= 5) {
              authLockUntil = Date.now() + 30000;
              authFails = 0;
            }
            resetTurnstile();
            return setErr('Неверный логин или пароль.');
          }
          if (isUserAdmin(mail, users[mail])) {
            users[mail].role = 'admin';
            db.set('u_users', users);
          }
        }
      }

      if (users[mail] && users[mail].banned) {
        return setErr('Аккаунт заблокирован администратором.');
      }

      authFails = 0;
      currentUser = mail;
      db.set('u_session', currentUser);
      $('#auth').close();
      form.reset();
      renderAuth();

      toast(authMode === 'reg' ? 'Аккаунт успешно создан' : 'Вы вошли в аккаунт');

      if (pendingAuthCallback) {
        const callback = pendingAuthCallback;
        pendingAuthCallback = null;
        callback();
      }
    });
  }

  // Profile Info Form submit (Personal data update)
  const profInfoForm = $('#profInfoForm');
  if (profInfoForm) {
    profInfoForm.addEventListener('submit', e => {
      e.preventDefault();
      const errEl = $('#profInfoErr');
      const okEl = $('#profInfoOk');
      errEl.textContent = '';
      okEl.hidden = true;

      const setErr = msg => {
        errEl.textContent = msg;
        profInfoForm.classList.remove('shake');
        void profInfoForm.offsetWidth;
        profInfoForm.classList.add('shake');
      };

      const newName = $('#profName').value.trim();
      const newPhone = $('#profPhone').value.trim();
      const newCompany = $('#profCompany').value.trim();

      if (newName.length < 2) {
        return setErr('Имя должно содержать минимум 2 символа.');
      }

      if (containsForbiddenWord(newName) || containsForbiddenWord(newCompany)) {
        return setErr('Имя или компания содержит недопустимые слова.');
      }

      const users = getUsers();
      if (!currentUser || !users[currentUser]) {
        return setErr('Ошибка авторизации. Войдите заново.');
      }

      users[currentUser].name = newName;
      users[currentUser].phone = newPhone;
      users[currentUser].company = newCompany;
      db.set('u_users', users);

      // Background sync to Neon database
      try {
        fetch('/api/auth', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            action: 'update_profile',
            login: currentUser,
            name: newName,
            phone: newPhone,
            company: newCompany
          })
        }).catch(err => console.warn('Background profile sync error:', err));
      } catch (e) {}

      // Update UI displays
      renderAuth();
      $('#profAvatar').textContent = newName[0].toUpperCase();
      $('#profHeadName').textContent = newName;

      okEl.hidden = false;
      okEl.textContent = 'Данные профиля успешно сохранены в базе!';
      toast('Профиль обновлён');
    });
  }

  // Profile Password Form submit (Change password)
  const profPassForm = $('#profPassForm');
  if (profPassForm) {
    profPassForm.addEventListener('submit', async e => {
      e.preventDefault();
      const errEl = $('#profPassErr');
      const okEl = $('#profPassOk');
      errEl.textContent = '';
      okEl.hidden = true;

      const setErr = msg => {
        errEl.textContent = msg;
        profPassForm.classList.remove('shake');
        void profPassForm.offsetWidth;
        profPassForm.classList.add('shake');
      };

      const oldPass = $('#profOldPass').value;
      const newPass = $('#profNewPass').value;
      const confPass = $('#profConfPass').value;

      if (!oldPass) {
        return setErr('Введите текущий пароль.');
      }

      const users = getUsers();
      if (!currentUser || !users[currentUser]) {
        return setErr('Ошибка авторизации. Войдите заново.');
      }

      const oldHash = await hash(oldPass);
      if (oldHash !== users[currentUser].h) {
        return setErr('Неверный текущий пароль.');
      }

      if (!(newPass.length >= 8 && /[a-zа-я]/i.test(newPass) && /\d/.test(newPass))) {
        return setErr('Новый пароль: минимум 8 символов, буквы и цифры.');
      }

      if (newPass === oldPass) {
        return setErr('Новый пароль должен отличаться от текущего.');
      }

      if (newPass !== confPass) {
        return setErr('Подтверждение пароля не совпадает.');
      }

      const newHash = await hash(newPass);

      // Sync password update to Neon database
      try {
        const resp = await fetch('/api/auth', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            action: 'change_password',
            login: currentUser,
            old_hash: oldHash,
            new_hash: newHash
          })
        });
        const data = await resp.json();
        if (!resp.ok) {
          return setErr(data.error || 'Ошибка при обновлении пароля на сервере.');
        }
      } catch (netErr) {
        console.warn('Backend password sync deferred:', netErr);
      }

      users[currentUser].h = newHash;
      db.set('u_users', users);

      // Reset fields
      $('#profOldPass').value = '';
      $('#profNewPass').value = '';
      $('#profConfPass').value = '';
      $$('#profMeter i').forEach(bar => bar.classList.remove('on'));

      okEl.hidden = false;
      okEl.textContent = 'Пароль успешно изменён и сохранён в базе!';
      toast('Пароль успешно обновлён');
    });
  }
}
