document.addEventListener('DOMContentLoaded', () => {
    // --- State Variables ---
    let categoryChart = null;
    let currentTab = 'tab-dashboard';

    // --- DOM Elements ---
    const tabs = document.querySelectorAll('.nav-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    // Modals
    const modalTx = document.getElementById('modal-transaction');
    const modalRec = document.getElementById('modal-recurring');
    const modalGoal = document.getElementById('modal-goal');
    const modalDebt = document.getElementById('modal-debt');

    // Forms
    const formTx = document.getElementById('form-transaction');
    const formRec = document.getElementById('form-recurring');
    const formGoal = document.getElementById('form-goal');
    const formDebt = document.getElementById('form-debt');

    // Buttons to Open Modals
    const btnAddTx = document.getElementById('btn-add-transaction');
    const btnAddRec = document.getElementById('btn-add-recurring');
    const btnEditGoal = document.getElementById('btn-edit-goal');
    const btnAddDebt = document.getElementById('btn-add-debt');
    
    // Quick Actions
    const quickAddIncome = document.getElementById('quick-add-income');
    const quickAddExpense = document.getElementById('quick-add-expense');
    const quickAddService = document.getElementById('quick-add-service');

    // Close Buttons
    const closeBtns = document.querySelectorAll('.modal-close, .btn-secondary');

    // Filter Elements
    const filterType = document.getElementById('filter-type');
    const filterCategory = document.getElementById('filter-category');
    const btnClearFilters = document.getElementById('btn-clear-filters');

    // --- Response Interceptor Helper ---
    function handleResponse(res) {
        if (res.status === 401) {
            window.location.href = '/login';
            throw new Error('Sesión expirada. Redirigiendo...');
        }
        return res;
    }

    // --- Tab Switching ---
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.getAttribute('data-tab');
            switchTab(targetTab);
        });
    });

    function switchTab(tabId) {
        tabs.forEach(t => t.classList.remove('active'));
        tabPanes.forEach(p => p.classList.remove('active'));

        const activeTab = document.querySelector(`[data-tab="${tabId}"]`);
        const activePane = document.getElementById(tabId);
        
        if (activeTab) activeTab.classList.add('active');
        if (activePane) activePane.classList.add('active');
        
        currentTab = tabId;

        // Fetch fresh data based on active tab
        if (tabId === 'tab-dashboard') {
            loadDashboardData();
        } else if (tabId === 'tab-transactions') {
            loadTransactions();
        } else if (tabId === 'tab-recurring') {
            loadRecurring();
        } else if (tabId === 'tab-debts') {
            loadDebts();
        }
    }

    // --- Modal Handlers ---
    function openModal(modal) {
        modal.classList.add('active');
    }

    function closeModal(modal) {
        modal.classList.remove('active');
        // Reset forms if it is one of the modals
        if (modal === modalTx) {
            formTx.reset();
            document.getElementById('tx-id').value = '';
            document.getElementById('modal-transaction-title').innerText = 'Nueva Transacción';
            setTodayDate('tx-date');
        } else if (modal === modalRec) {
            formRec.reset();
            document.getElementById('rec-id').value = '';
            document.getElementById('modal-recurring-title').innerText = 'Registrar Servicio Recurrente';
            setTodayDate('rec-date');
        } else if (modal === modalGoal) {
            formGoal.reset();
        } else if (modal === modalDebt) {
            formDebt.reset();
            document.getElementById('debt-id').value = '';
            document.getElementById('modal-debt-title').innerText = 'Registrar Deuda / Préstamo';
            document.getElementById('debt-status').value = 'pending';
            setTodayDate('debt-date');
        }
    }

    // Helper: set date input to today
    function setTodayDate(elementId) {
        const today = new Date().toISOString().split('T')[0];
        const el = document.getElementById(elementId);
        if (el) el.value = today;
    }

    // Set up close actions for all modals
    closeBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const openModalEl = btn.closest('.modal');
            if (openModalEl) closeModal(openModalEl);
        });
    });

    // Handle clicks outside the modal content to close it
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            closeModal(e.target);
        }
    });

    // --- Open Modal Button Listeners ---
    btnAddTx.addEventListener('click', () => {
        openModal(modalTx);
        setTodayDate('tx-date');
    });

    btnAddRec.addEventListener('click', () => {
        openModal(modalRec);
        setTodayDate('rec-date');
    });

    if (btnAddDebt) {
        btnAddDebt.addEventListener('click', () => {
            openModal(modalDebt);
            setTodayDate('debt-date');
        });
    }

    // Quick Actions
    quickAddIncome.addEventListener('click', () => {
        openModal(modalTx);
        document.getElementById('tx-type').value = 'income';
        document.getElementById('tx-category').value = 'Trabajo / Inversión';
        setTodayDate('tx-date');
    });

    quickAddExpense.addEventListener('click', () => {
        openModal(modalTx);
        document.getElementById('tx-type').value = 'expense';
        document.getElementById('tx-category').value = 'Gasto Hormiga';
        setTodayDate('tx-date');
    });

    quickAddService.addEventListener('click', () => {
        openModal(modalRec);
        setTodayDate('rec-date');
    });

    btnEditGoal.addEventListener('click', () => {
        fetch('/api/goals')
            .then(handleResponse)
            .then(res => res.json())
            .then(data => {
                document.getElementById('goal-week-start').value = data.week_start_date;
                document.getElementById('goal-income').value = data.target_income || 0;
                document.getElementById('goal-savings').value = data.target_savings || 0;
                openModal(modalGoal);
            })
            .catch(err => console.error('Error al cargar metas:', err));
    });


    // --- FORMATTING HELPERS ---
    const formatCurrency = (val) => {
        return new Intl.NumberFormat('es-MX', {
            style: 'currency',
            currency: 'MXN'
        }).format(val || 0);
    };


    // --- DATA LOADING: DASHBOARD ---
    function loadDashboardData() {
        fetch('/api/summary')
            .then(handleResponse)
            .then(res => res.json())
            .then(data => {
                // Main KPIs
                document.getElementById('kpi-net-balance').innerText = formatCurrency(data.net_balance);
                document.getElementById('kpi-total-income').innerText = formatCurrency(data.total_income);
                document.getElementById('kpi-total-expenses').innerText = formatCurrency(data.total_expense);
                document.getElementById('kpi-weekend-expenses').innerText = formatCurrency(data.weekend_expenses);

                // Balance Trend/Color
                const balanceKpi = document.getElementById('kpi-net-balance');
                if (data.net_balance >= 0) {
                    balanceKpi.style.color = 'var(--success)';
                } else {
                    balanceKpi.style.color = 'var(--danger)';
                }

                // Credit & Debit details
                document.getElementById('val-credit-expenses').innerText = formatCurrency(data.credit_expenses);
                document.getElementById('val-debit-expenses').innerText = formatCurrency(data.debit_expenses);
                
                const totalExp = data.credit_expenses + data.debit_expenses;
                let creditPct = 0;
                let debitPct = 0;
                if (totalExp > 0) {
                    creditPct = (data.credit_expenses / totalExp) * 100;
                    debitPct = (data.debit_expenses / totalExp) * 100;
                }
                
                document.getElementById('bar-credit-expenses').style.width = `${creditPct}%`;
                document.getElementById('bar-debit-expenses').style.width = `${debitPct}%`;

                // Weekly Goal Progress Bar
                const prog = data.weekly_progress;
                const actualInc = prog.actual_income || 0;
                const targetInc = prog.target_income || 0;
                const actualSav = prog.actual_savings || 0;
                const targetSav = prog.target_savings || 0;

                document.getElementById('lbl-goal-income-progress').innerText = `${formatCurrency(actualInc)} / ${formatCurrency(targetInc)}`;
                document.getElementById('lbl-goal-savings-progress').innerText = `${formatCurrency(actualSav)} / ${formatCurrency(targetSav)}`;

                const incPct = targetInc > 0 ? Math.min((actualInc / targetInc) * 100, 100) : 0;
                const savPct = targetSav > 0 ? Math.min((actualSav / targetSav) * 100, 100) : 0;

                document.getElementById('bar-goal-income').style.width = `${incPct}%`;
                document.getElementById('bar-goal-savings').style.width = `${savPct}%`;

                // Render Payment Notifications
                const notifBox = document.getElementById('payments-notification-box');
                const notifList = document.getElementById('notification-alerts-list');
                
                if (data.upcoming_alerts && data.upcoming_alerts.length > 0) {
                    notifBox.style.display = 'block';
                    notifList.innerHTML = '';
                    
                    data.upcoming_alerts.forEach(alert => {
                        const div = document.createElement('div');
                        let colorClass = 'alert-green-blue';
                        let badgeText = '';

                        if (alert.days_left <= 2) {
                            colorClass = 'alert-red';
                            badgeText = alert.days_left === 0 ? '¡Paga Hoy!' : `¡Faltan ${alert.days_left} días!`;
                        } else if (alert.days_left <= 5) {
                            colorClass = 'alert-yellow';
                            badgeText = `Vence en ${alert.days_left} días`;
                        } else {
                            colorClass = 'alert-green-blue';
                            badgeText = `Vence en ${alert.days_left} días`;
                        }

                        div.className = `alert-item ${colorClass}`;
                        div.innerHTML = `
                            <div class="alert-info-content">
                                <span class="alert-service-name">${alert.name}</span>
                                <span class="alert-service-details">Cobro de: <strong>${formatCurrency(alert.amount)}</strong> &bull; Vence el <strong>${alert.next_billing_date}</strong></span>
                            </div>
                            <span class="alert-status-badge">${badgeText}</span>
                        `;
                        notifList.appendChild(div);
                    });
                } else {
                    notifBox.style.display = 'none';
                }

                // Daily Summary Status Text
                const statusBox = document.getElementById('daily-status-text');
                let statusMsg = `Esta semana (lunes a domingo) has acumulado **${formatCurrency(actualInc)}** en ingresos. `;
                if (targetInc > 0) {
                    if (actualInc >= targetInc) {
                        statusMsg += `¡Excelente trabajo! Has superado tu meta de ingresos de la semana por ${formatCurrency(actualInc - targetInc)}.`;
                    } else {
                        const remaining = targetInc - actualInc;
                        statusMsg += `Te faltan ${formatCurrency(remaining)} para alcanzar tu objetivo de ingresos semanal.`;
                    }
                } else {
                    statusMsg += 'No has definido una meta de ingresos para esta semana aún.';
                }
                
                const owedToMe = data.total_owed_to_me || 0;
                const iOwe = data.total_i_owe || 0;
                if (owedToMe > 0 || iOwe > 0) {
                    statusMsg += `<br><br><i class="fa-solid fa-handshake"></i> <strong>Estatus de Deudas:</strong> `;
                    if (owedToMe > 0) statusMsg += `Te deben un total de <strong>${formatCurrency(owedToMe)}</strong>. `;
                    if (iOwe > 0) statusMsg += `Debes a otras personas un total de <strong>${formatCurrency(iOwe)}</strong>.`;
                }

                if (data.weekend_expenses > 0) {
                    statusMsg += `<br><br><span class="text-warning"><i class="fa-solid fa-triangle-exclamation"></i> Tus gastos acumulados los fines de semana ascienden a <strong>${formatCurrency(data.weekend_expenses)}</strong>. Vigila que no sobrepasen tus ahorros.</span>`;
                }

                statusBox.innerHTML = statusMsg;

                // Load Chart.js Donut
                updateCategoryChart(data.categories_breakdown);
            })
            .catch(err => console.error('Error al cargar datos del Dashboard:', err));
    }

    function updateCategoryChart(categoriesData) {
        const ctx = document.getElementById('chart-categories').getContext('2d');
        
        if (categoryChart) {
            categoryChart.destroy();
        }

        const labels = Object.keys(categoriesData);
        const data = Object.values(categoriesData);

        if (labels.length === 0) {
            categoryChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Sin gastos registrados'],
                    datasets: [{
                        data: [1],
                        backgroundColor: ['#e2e8f0'],
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
            return;
        }

        const categoryColors = {
            'Trabajo / Inversión': '#1e40af',
            'Gasto Hormiga': '#ef4444',
            'Suscripción': '#8b5cf6',
            'Servicio': '#f59e0b',
            'Fin de Semana': '#f43f5e',
            'Ahorro': '#10b981',
            'Otros': '#64748b'
        };

        const bgColors = labels.map(label => categoryColors[label] || '#3b82f6');

        categoryChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Gastos',
                    data: data,
                    backgroundColor: bgColors,
                    borderWidth: 1,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: { family: 'Plus Jakarta Sans', size: 11 },
                            padding: 15
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return ` ${context.label}: ${formatCurrency(context.raw)}`;
                            }
                        }
                    }
                },
                cutout: '65%'
            }
        });
    }


    // --- DATA LOADING: TRANSACTIONS ---
    function loadTransactions() {
        const type = filterType.value;
        const category = filterCategory.value;
        
        let url = '/api/transactions';
        const params = [];
        if (type) params.push(`type=${type}`);
        if (category) params.push(`category=${encodeURIComponent(category)}`);
        
        if (params.length > 0) {
            url += '?' + params.join('&');
        }

        fetch(url)
            .then(handleResponse)
            .then(res => res.json())
            .then(data => {
                const listContainer = document.getElementById('transactions-list');
                listContainer.innerHTML = '';

                if (data.length === 0) {
                    listContainer.innerHTML = '<tr><td colspan="7" class="text-center py-4">No se encontraron transacciones.</td></tr>';
                    return;
                }

                data.forEach(tx => {
                    const tr = document.createElement('tr');
                    
                    const badgeType = tx.type === 'income' ? 'badge-income' : 'badge-expense';
                    const labelType = tx.type === 'income' ? 'Ingreso' : 'Egreso';
                    const amountSign = tx.type === 'income' ? '+' : '-';
                    const amountClass = tx.type === 'income' ? 'badge-income' : 'badge-expense';

                    tr.innerHTML = `
                        <td data-label="Fecha">${tx.date}</td>
                        <td data-label="Descripción" style="font-weight: 600;">${tx.description}</td>
                        <td data-label="Categoría"><span class="badge badge-category">${tx.category}</span></td>
                        <td data-label="Método"><span class="badge badge-method">${tx.payment_method}</span></td>
                        <td data-label="Tipo"><span class="badge ${badgeType}">${labelType}</span></td>
                        <td data-label="Monto" class="text-right" style="font-weight: 700;">
                            <span class="${amountClass}">${amountSign} ${formatCurrency(tx.amount)}</span>
                        </td>
                        <td data-label="Acciones" class="text-center">
                            <div class="action-buttons">
                                <button class="btn-icon btn-edit" onclick="editTransaction(${tx.id})" title="Editar"><i class="fa-solid fa-pen-to-square"></i></button>
                                <button class="btn-icon btn-delete" onclick="deleteTransaction(${tx.id})" title="Eliminar"><i class="fa-solid fa-trash-can"></i></button>
                            </div>
                        </td>
                    `;
                    listContainer.appendChild(tr);
                });
            })
            .catch(err => console.error('Error al cargar transacciones:', err));
    }

    filterType.addEventListener('change', loadTransactions);
    filterCategory.addEventListener('change', loadTransactions);
    btnClearFilters.addEventListener('click', () => {
        filterType.value = '';
        filterCategory.value = '';
        loadTransactions();
    });


    // --- DATA LOADING: RECURRING SERVICES ---
    function loadRecurring() {
        fetch('/api/recurring')
            .then(handleResponse)
            .then(res => res.json())
            .then(data => {
                const listContainer = document.getElementById('recurring-list');
                const monthlyTotalEl = document.getElementById('est-monthly-recurring');
                const countEl = document.getElementById('count-recurring');
                
                listContainer.innerHTML = '';
                countEl.innerText = data.length;

                let monthlySum = 0;

                if (data.length === 0) {
                    listContainer.innerHTML = '<p class="text-center py-4 text-muted">No has registrado servicios recurrentes aún. Registra uno arriba para planificar tus finanzas.</p>';
                    monthlyTotalEl.innerText = formatCurrency(0);
                    return;
                }

                data.forEach(service => {
                    let monthlyContribution = service.amount;
                    if (service.frequency === 'Semanal') {
                        monthlyContribution = service.amount * 4.33;
                    } else if (service.frequency === 'Anual') {
                        monthlyContribution = service.amount / 12;
                    }
                    monthlySum += monthlyContribution;

                    const item = document.createElement('div');
                    item.className = 'recurring-item-card';

                    let iconClass = 'fa-solid fa-calendar';
                    let iconColorClass = '';
                    if (service.category === 'Suscripción') {
                        iconClass = 'fa-solid fa-play';
                    } else if (service.category === 'Servicio') {
                        iconClass = 'fa-solid fa-bolt-lightning';
                        iconColorClass = 'service-icon';
                    } else if (service.category === 'Trabajo / Inversión') {
                        iconClass = 'fa-solid fa-briefcase';
                    }

                    const freqClass = `freq-${service.frequency.toLowerCase()}`;

                    item.innerHTML = `
                        <div class="recurring-info-group">
                            <div class="recurring-icon ${iconColorClass}">
                                <i class="${iconClass}"></i>
                            </div>
                            <div class="recurring-meta">
                                <h4>${service.name}</h4>
                                <p><i class="fa-solid fa-circle-info"></i> Método: ${service.payment_method} &bull; Próximo cobro: <strong>${service.next_billing_date}</strong></p>
                            </div>
                        </div>
                        <div class="recurring-details">
                            <span class="freq-tag ${freqClass}">${service.frequency}</span>
                            <span class="recurring-amount">${formatCurrency(service.amount)}</span>
                            <div class="action-buttons">
                                <button class="btn-icon btn-edit" onclick="editRecurring(${service.id})" title="Editar"><i class="fa-solid fa-pen-to-square"></i></button>
                                <button class="btn-icon btn-delete" onclick="deleteRecurring(${service.id})" title="Eliminar"><i class="fa-solid fa-trash-can"></i></button>
                            </div>
                        </div>
                    `;
                    listContainer.appendChild(item);
                });

                monthlyTotalEl.innerText = formatCurrency(monthlySum);
            })
            .catch(err => console.error('Error al cargar servicios recurrentes:', err));
    }


    // --- DATA LOADING: DEBTS ---
    function loadDebts() {
        fetch('/api/debts')
            .then(handleResponse)
            .then(res => res.json())
            .then(data => {
                const lendList = document.getElementById('debts-lend-list');
                const borrowList = document.getElementById('debts-borrow-list');
                const kpiLend = document.getElementById('kpi-total-owed-to-me');
                const kpiBorrow = document.getElementById('kpi-total-i-owe');
                
                lendList.innerHTML = '';
                borrowList.innerHTML = '';

                let totalLend = 0;
                let totalBorrow = 0;

                const lendRows = data.filter(d => d.type === 'lend');
                const borrowRows = data.filter(d => d.type === 'borrow');

                if (lendRows.length === 0) {
                    lendList.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">No tienes registros de personas que te deban dinero.</td></tr>';
                } else {
                    lendRows.forEach(d => {
                        if (d.status === 'pending') {
                            totalLend += d.amount;
                        }
                        
                        const tr = document.createElement('tr');
                        if (d.status === 'paid') {
                            tr.style.opacity = '0.55';
                            tr.style.textDecoration = 'line-through';
                        }
                        
                        const badgeStatusClass = d.status === 'pending' ? 'badge-expense' : 'badge-income';
                        const labelStatus = d.status === 'pending' ? 'Pendiente' : 'Pagado';
                        const checkIcon = d.status === 'pending' ? 'fa-circle-check' : 'fa-clock';
                        const checkTooltip = d.status === 'pending' ? 'Marcar como Pagado' : 'Marcar como Pendiente';

                        tr.innerHTML = `
                            <td data-label="Persona" style="font-weight: 600;">${d.person_name}</td>
                            <td data-label="Concepto">${d.description || '-'}</td>
                            <td data-label="Vencimiento">${d.due_date || 'Sin fecha'}</td>
                            <td data-label="Monto" class="text-right" style="font-weight: 700; color: var(--success);">${formatCurrency(d.amount)}</td>
                            <td data-label="Estado" class="text-center"><span class="badge ${badgeStatusClass}">${labelStatus}</span></td>
                            <td data-label="Acciones" class="text-center">
                                <div class="action-buttons">
                                    <button class="btn-icon btn-edit" onclick="toggleDebtStatus(${d.id}, '${d.status}')" title="${checkTooltip}"><i class="fa-solid ${checkIcon}"></i></button>
                                    <button class="btn-icon btn-edit" onclick="editDebt(${d.id})" title="Editar"><i class="fa-solid fa-pen-to-square"></i></button>
                                    <button class="btn-icon btn-delete" onclick="deleteDebt(${d.id})" title="Eliminar"><i class="fa-solid fa-trash-can"></i></button>
                                </div>
                            </td>
                        `;
                        lendList.appendChild(tr);
                    });
                }

                if (borrowRows.length === 0) {
                    borrowList.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">No has registrado deudas de personas a las que debas.</td></tr>';
                } else {
                    borrowRows.forEach(d => {
                        if (d.status === 'pending') {
                            totalBorrow += d.amount;
                        }
                        
                        const tr = document.createElement('tr');
                        if (d.status === 'paid') {
                            tr.style.opacity = '0.55';
                            tr.style.textDecoration = 'line-through';
                        }
                        
                        const badgeStatusClass = d.status === 'pending' ? 'badge-expense' : 'badge-income';
                        const labelStatus = d.status === 'pending' ? 'Pendiente' : 'Pagado';
                        const checkIcon = d.status === 'pending' ? 'fa-circle-check' : 'fa-clock';
                        const checkTooltip = d.status === 'pending' ? 'Marcar como Pagado' : 'Marcar como Pendiente';

                        tr.innerHTML = `
                            <td data-label="A quién debo" style="font-weight: 600;">${d.person_name}</td>
                            <td data-label="Concepto">${d.description || '-'}</td>
                            <td data-label="Vencimiento">${d.due_date || 'Sin fecha'}</td>
                            <td data-label="Monto" class="text-right" style="font-weight: 700; color: var(--danger);">${formatCurrency(d.amount)}</td>
                            <td data-label="Estado" class="text-center"><span class="badge ${badgeStatusClass}">${labelStatus}</span></td>
                            <td data-label="Acciones" class="text-center">
                                <div class="action-buttons">
                                    <button class="btn-icon btn-edit" onclick="toggleDebtStatus(${d.id}, '${d.status}')" title="${checkTooltip}"><i class="fa-solid ${checkIcon}"></i></button>
                                    <button class="btn-icon btn-edit" onclick="editDebt(${d.id})" title="Editar"><i class="fa-solid fa-pen-to-square"></i></button>
                                    <button class="btn-icon btn-delete" onclick="deleteDebt(${d.id})" title="Eliminar"><i class="fa-solid fa-trash-can"></i></button>
                                </div>
                            </td>
                        `;
                        borrowList.appendChild(tr);
                    });
                }

                kpiLend.innerText = formatCurrency(totalLend);
                kpiBorrow.innerText = formatCurrency(totalBorrow);
            })
            .catch(err => console.error('Error al cargar deudas:', err));
    }


    // --- FORM SUBMISSIONS (CREATE / UPDATE) ---

    // 1. Transaction Form
    formTx.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const id = document.getElementById('tx-id').value;
        const payload = {
            date: document.getElementById('tx-date').value,
            description: document.getElementById('tx-description').value,
            amount: document.getElementById('tx-amount').value,
            type: document.getElementById('tx-type').value,
            category: document.getElementById('tx-category').value,
            payment_method: document.getElementById('tx-method').value
        };

        const method = id ? 'PUT' : 'POST';
        const url = id ? `/api/transactions/${id}` : '/api/transactions';

        fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(handleResponse)
        .then(res => {
            if (!res.ok) throw new Error('Error en el servidor al guardar la transacción.');
            return res.json();
        })
        .then(data => {
            closeModal(modalTx);
            if (currentTab === 'tab-dashboard') {
                loadDashboardData();
            } else if (currentTab === 'tab-transactions') {
                loadTransactions();
            }
        })
        .catch(err => {
            alert(err.message);
        });
    });

    // 2. Recurring Service Form
    formRec.addEventListener('submit', (e) => {
        e.preventDefault();

        const id = document.getElementById('rec-id').value;
        const payload = {
            name: document.getElementById('rec-name').value,
            amount: document.getElementById('rec-amount').value,
            frequency: document.getElementById('rec-frequency').value,
            next_billing_date: document.getElementById('rec-date').value,
            category: document.getElementById('rec-category').value,
            payment_method: document.getElementById('rec-method').value
        };

        const method = id ? 'PUT' : 'POST';
        const url = id ? `/api/recurring/${id}` : '/api/recurring';

        fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(handleResponse)
        .then(res => {
            if (!res.ok) throw new Error('Error al guardar el servicio recurrente.');
            return res.json();
        })
        .then(data => {
            closeModal(modalRec);
            loadRecurring();
        })
        .catch(err => {
            alert(err.message);
        });
    });

    // 3. Weekly Goal Form
    formGoal.addEventListener('submit', (e) => {
        e.preventDefault();

        const payload = {
            week_start_date: document.getElementById('goal-week-start').value,
            target_income: document.getElementById('goal-income').value,
            target_savings: document.getElementById('goal-savings').value
        };

        fetch('/api/goals', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(handleResponse)
        .then(res => {
            if (!res.ok) throw new Error('Error al guardar las metas semanales.');
            return res.json();
        })
        .then(data => {
            closeModal(modalGoal);
            loadDashboardData();
        })
        .catch(err => {
            alert(err.message);
        });
    });

    // 4. Debt Form
    formDebt.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const id = document.getElementById('debt-id').value;
        const payload = {
            person_name: document.getElementById('debt-person').value,
            amount: document.getElementById('debt-amount').value,
            type: document.getElementById('debt-type').value,
            due_date: document.getElementById('debt-date').value,
            description: document.getElementById('debt-description').value,
            status: document.getElementById('debt-status').value
        };

        const method = id ? 'PUT' : 'POST';
        const url = id ? `/api/debts/${id}` : '/api/debts';

        fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(handleResponse)
        .then(res => {
            if (!res.ok) throw new Error('Error en el servidor al guardar la deuda.');
            return res.json();
        })
        .then(data => {
            closeModal(modalDebt);
            loadDebts();
        })
        .catch(err => {
            alert(err.message);
        });
    });


    // --- GLOBAL SCOPE ACTIONS FOR TABLE/GRID ACTIONS ---
    
    // Edit Transaction
    window.editTransaction = function(id) {
        fetch(`/api/transactions`)
            .then(handleResponse)
            .then(res => res.json())
            .then(transactions => {
                const tx = transactions.find(t => t.id === id);
                if (tx) {
                    document.getElementById('tx-id').value = tx.id;
                    document.getElementById('tx-date').value = tx.date;
                    document.getElementById('tx-description').value = tx.description;
                    document.getElementById('tx-amount').value = tx.amount;
                    document.getElementById('tx-type').value = tx.type;
                    document.getElementById('tx-category').value = tx.category;
                    document.getElementById('tx-method').value = tx.payment_method;

                    document.getElementById('modal-transaction-title').innerText = 'Editar Transacción';
                    openModal(modalTx);
                }
            })
            .catch(err => console.error('Error al obtener transacción:', err));
    };

    // Delete Transaction
    window.deleteTransaction = function(id) {
        if (confirm('¿Estás seguro de que deseas eliminar esta transacción?')) {
            fetch(`/api/transactions/${id}`, {
                method: 'DELETE'
            })
            .then(handleResponse)
            .then(res => res.json())
            .then(() => {
                loadTransactions();
            })
            .catch(err => console.error('Error al eliminar transacción:', err));
        }
    };

    // Edit Recurring Service
    window.editRecurring = function(id) {
        fetch('/api/recurring')
            .then(handleResponse)
            .then(res => res.json())
            .then(services => {
                const s = services.find(item => item.id === id);
                if (s) {
                    document.getElementById('rec-id').value = s.id;
                    document.getElementById('rec-name').value = s.name;
                    document.getElementById('rec-amount').value = s.amount;
                    document.getElementById('rec-frequency').value = s.frequency;
                    document.getElementById('rec-date').value = s.next_billing_date;
                    document.getElementById('rec-category').value = s.category;
                    document.getElementById('rec-method').value = s.payment_method;

                    document.getElementById('modal-recurring-title').innerText = 'Editar Servicio Recurrente';
                    openModal(modalRec);
                }
            })
            .catch(err => console.error('Error al obtener servicio:', err));
    };

    // Delete Recurring Service
    window.deleteRecurring = function(id) {
        if (confirm('¿Estás seguro de que deseas eliminar este servicio recurrente?')) {
            fetch(`/api/recurring/${id}`, {
                method: 'DELETE'
            })
            .then(handleResponse)
            .then(res => res.json())
            .then(() => {
                loadRecurring();
            })
            .catch(err => console.error('Error al eliminar servicio:', err));
        }
    };

    // Toggle Debt Status (Pending <-> Paid)
    window.toggleDebtStatus = function(id, currentStatus) {
        const nextStatus = currentStatus === 'pending' ? 'paid' : 'pending';
        fetch(`/api/debts/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: nextStatus })
        })
        .then(handleResponse)
        .then(res => {
            if (!res.ok) throw new Error('Error al actualizar estatus de deuda.');
            return res.json();
        })
        .then(() => {
            loadDebts();
        })
        .catch(err => console.error('Error al alternar estatus de deuda:', err));
    };

    // Edit Debt
    window.editDebt = function(id) {
        fetch('/api/debts')
            .then(handleResponse)
            .then(res => res.json())
            .then(debts => {
                const d = debts.find(item => item.id === id);
                if (d) {
                    document.getElementById('debt-id').value = d.id;
                    document.getElementById('debt-person').value = d.person_name;
                    document.getElementById('debt-amount').value = d.amount;
                    document.getElementById('debt-type').value = d.type;
                    document.getElementById('debt-date').value = d.due_date;
                    document.getElementById('debt-description').value = d.description;
                    document.getElementById('debt-status').value = d.status;

                    document.getElementById('modal-debt-title').innerText = 'Editar Deuda / Préstamo';
                    openModal(modalDebt);
                }
            })
            .catch(err => console.error('Error al obtener deudas:', err));
    };

    // Delete Debt
    window.deleteDebt = function(id) {
        if (confirm('¿Estás seguro de que deseas eliminar este registro de deuda?')) {
            fetch(`/api/debts/${id}`, {
                method: 'DELETE'
            })
            .then(handleResponse)
            .then(res => res.json())
            .then(() => {
                loadDebts();
            })
            .catch(err => console.error('Error al eliminar deuda:', err));
        }
    };

    // --- INITIAL DATA LOAD ---
    loadDashboardData();
});
