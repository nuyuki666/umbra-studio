/* ==========================================================================
   Umbra Studio — Live Support Chat Widget
   ========================================================================== */

const chatHistory = db.get('chat', [
  {
    r: 'b',
    t: 'Здравствуйте! Подскажем по тарифам, срокам и оплате. Выберите тему или напишите вопрос.'
  }
]);

/**
 * Render message history into chat container
 */
function drawChatMessages() {
  const msgsEl = $('#msgs');
  if (!msgsEl) return;
  msgsEl.innerHTML = chatHistory
    .map(m => `<div class="m ${m.r}">${esc(m.t)}</div>`)
    .join('');
  msgsEl.scrollTop = 1e6;
}

/**
 * Append message and persist
 */
function sayChatMessage(role, text) {
  chatHistory.push({ r: role, t: text });
  db.set('chat', chatHistory.slice(-60));
  drawChatMessages();
}

/**
 * Dynamic intelligent bot responses
 */
function getBotResponse(input) {
  const text = input.toLowerCase();
  const plans = cfg.plans;

  if (/привет|здравств/.test(text)) {
    return 'Здравствуйте! Чем помочь?';
  }
  if (/цен|стоим|сколько|прайс/.test(text)) {
    return `Лендинг — от ${fmt(plans['Лендинг'])}, многостраничный сайт — от ${fmt(
      plans['Многостраничный сайт']
    )}, магазин — от ${fmt(
      plans['Интернет-магазин']
    )}. В заказе можно указать свою сумму в поле «Бюджет».`;
  }
  if (/срок|долго|когда|быстр/.test(text)) {
    return 'Лендинг делаем от 3 дней, многостраничный сайт — от 7, магазин — от 10. Первый экран показываем уже через 24–48 часов.';
  }
  if (/оплат|предоплат|карт|договор/.test(text)) {
    return 'Предоплата 50%, остаток — после утверждения макетов. Договор и акт выдаём.';
  }
  if (/оператор|человек|менеджер/.test(text)) {
    return 'Позвал оператора. Обычно отвечаем в течение 15 минут в рабочее время (10:00–19:00 МСК).';
  }
  return 'Принял. Передал вопрос оператору — ответ придёт в этот чат.';
}

/**
 * User question processing with typing indicator
 */
function askChatMessage(text) {
  if (!text || !text.trim()) return;
  const cleanText = text.trim();
  sayChatMessage('u', cleanText);

  const msgsEl = $('#msgs');
  if (!msgsEl) return;

  const typingIndicator = document.createElement('div');
  typingIndicator.className = 'm b t';
  typingIndicator.textContent = 'Печатает…';
  msgsEl.append(typingIndicator);
  msgsEl.scrollTop = 1e6;

  setTimeout(() => {
    typingIndicator.remove();
    sayChatMessage('b', getBotResponse(cleanText));
  }, 700 + Math.random() * 500);
}

/**
 * Initialize Chat Widget
 */
function initChat() {
  const chatBtn = $('#chatBtn');
  const chatWindow = $('#chat');
  const chatClose = $('#chatX');
  const chatForm = $('#cf2');
  const chatInput = $('#cIn');
  const quickQuestions = $('.qs');

  if (chatBtn && chatWindow) {
    chatBtn.onclick = () => {
      const isOpen = chatWindow.classList.toggle('open');
      chatBtn.classList.toggle('active', isOpen);
      if (isOpen) {
        drawChatMessages();
        if (chatInput) chatInput.focus();
      }
    };
  }

  if (chatClose && chatWindow) {
    chatClose.onclick = () => {
      chatWindow.classList.remove('open');
      if (chatBtn) chatBtn.classList.remove('active');
    };
  }

  if (chatForm && chatInput) {
    chatForm.addEventListener('submit', e => {
      e.preventDefault();
      askChatMessage(chatInput.value);
      chatInput.value = '';
    });
  }

  if (quickQuestions) {
    quickQuestions.addEventListener('click', e => {
      const btn = e.target.closest('button');
      if (btn) askChatMessage(btn.textContent);
    });
  }

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && chatWindow) {
      chatWindow.classList.remove('open');
      if (chatBtn) chatBtn.classList.remove('active');
    }
  });
}
