/* ==========================================================================
   Umbra Studio — Orders & Checkout Logic
   ========================================================================== */

/**
 * Calculate dynamic budget string
 */
function getBudgetValue() {
  const oBud = $('#oBud');
  const oSum = $('#oSum');
  if (oBud && oBud.value === 'Своя сумма') {
    return 'Своя сумма: ' + fmt((oSum && oSum.value) || 0);
  }
  return oBud ? oBud.value : '';
}

/**
 * Open Order Success Modal
 */
function openOrderSuccessModal(id) {
  const okText = $('#okT');
  if (okText) {
    okText.textContent = `Номер заявки ${id}. Мы свяжемся с вами по указанным контактам.`;
  }
  const okDialog = $('#okd');
  if (okDialog) {
    okDialog.showModal();
  }
}

/**
 * List orders for the currently signed-in user
 */
function listOrders() {
  const renderList = (items) => {
    const listEl = $('#ordList');
    if (!listEl) return;
    listEl.innerHTML = items.length
      ? items
          .map(
            o =>
              `<div class="ord"><span class="st">${o.status || 'Новый'}</span><b>${o.id} · ${esc(o.type || o.service_plan || 'Проект')}</b><br><small>${esc(o.name || o.client_name || 'Клиент')} · ${o.date || (o.created_at ? new Date(o.created_at).toLocaleDateString('ru-RU') : '')}${o.quote ? ` · наша цена: ${fmt(o.quote)}` : ''}</small></div>`
          )
          .join('')
      : '<p class="note" style="text-align:left">Заказов пока нет. Заполните форму выше — он появится здесь.</p>';
  };

  const localOrders = getOrders().filter(o => o.user === currentUser);
  renderList(localOrders);

  if (currentUser) {
    fetch('/api/orders?email=' + encodeURIComponent(currentUser))
      .then(res => res.json())
      .then(data => {
        if (data.ok && Array.isArray(data.orders) && data.orders.length > 0) {
          renderList(data.orders);
        }
      })
      .catch(() => {});
  }
}

/**
 * Initialize Orders Functionality
 */
function initOrders() {
  const orderForm = $('#orderForm');
  const oBud = $('#oBud');
  const oSum = $('#oSum');

  // Dynamic budget input toggle
  if (oBud && oSum) {
    oBud.onchange = () => {
      const isCustom = oBud.value === 'Своя сумма';
      oSum.hidden = !isCustom;
      if (isCustom) {
        oSum.focus({ preventScroll: true });
      }
    };
  }

  // Reset form helper
  if (orderForm && oSum) {
    orderForm.addEventListener('reset', () => {
      setTimeout(() => {
        oSum.hidden = true;
      }, 0);
    });
  }

  // Order submission
  if (orderForm) {
    orderForm.addEventListener('submit', e => {
      e.preventDefault();
      const err = $('#oErr');
      if (err) err.textContent = '';

      const triggerError = msg => {
        if (err) err.textContent = msg;
        orderForm.classList.remove('shake');
        void orderForm.offsetWidth;
        orderForm.classList.add('shake');
      };

      if (!cfg.open) {
        return triggerError(cfg.msg || 'Приём заказов закрыт.');
      }

      const name = $('#oName').value.trim();
      const desc = $('#oDesc').value.trim();
      const con = $('#oCon').value.trim();

      if (!name) {
        return triggerError('Укажите название проекта или компании.');
      }
      if (desc.length < 20) {
        return triggerError('Опишите задачу подробнее — минимум 20 символов.');
      }
      if (!con) {
        return triggerError('Оставьте Telegram или телефон для связи.');
      }
      if (oBud && oBud.value === 'Своя сумма' && !(+oSum.value >= 100)) {
        return triggerError('Укажите свою сумму — от 100 ₽.');
      }

      const sendOrder = () => {
        const users = getUsers();
        if (users[currentUser]?.banned) {
          toast('Аккаунт заблокирован администратором');
          return;
        }

        const ordersList = getOrders();
        const newOrder = {
          id: '№' + (Date.now() % 1e6),
          user: currentUser,
          status: 'Новый',
          quote: 0,
          type: $('#oType').value,
          bud: getBudgetValue(),
          name,
          desc,
          con,
          date: new Date().toLocaleDateString('ru-RU')
        };

        // Sync order to Neon PostgreSQL
        try {
          fetch('/api/orders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              action: 'create',
              order: {
                id: newOrder.id,
                user_email: currentUser,
                service_plan: newOrder.type,
                price: parseInt(String(newOrder.bud).replace(/\D/g, '') || 5000, 10),
                client_name: newOrder.name,
                contact: newOrder.con,
                description: newOrder.desc
              }
            })
          }).catch(err => console.warn('Order cloud sync deferred:', err));
        } catch (e) {}

        ordersList.unshift(newOrder);
        db.set('orders', ordersList);
        orderForm.reset();
        openOrderSuccessModal(newOrder.id);
      };

      if (!currentUser) {
        openAuth('login', 'Войдите или создайте аккаунт — заказ отправится автоматически.', sendOrder);
      } else {
        sendOrder();
      }
    });
  }

  // Global actions for ordering and dialogs
  document.addEventListener('click', e => {
    const target = e.target.closest('button, a');
    if (!target) return;

    // "Мои заказы" button in header
    if (target.id === 'myOrd') {
      listOrders();
      const ordersDialog = $('#orders');
      if (ordersDialog) ordersDialog.showModal();
    }

    // Tariff cards "Заказать" button
    if (target.dataset.plan) {
      const oType = $('#oType');
      if (oType) oType.value = target.dataset.plan;

      const orderSection = $('#order');
      if (orderSection) orderSection.scrollIntoView({ behavior: 'smooth' });

      if (orderForm) {
        orderForm.classList.remove('flash');
        void orderForm.offsetWidth; // trigger reflow
        orderForm.classList.add('flash');
      }
    }

    // Dialog close buttons
    if (target.hasAttribute('data-close')) {
      const dialog = target.closest('dialog');
      if (dialog) dialog.close();
    }
  });

  // Close modals when clicking backdrop
  $$('dialog').forEach(d => {
    d.addEventListener('click', e => {
      if (e.target === d) d.close();
    });
  });
}
