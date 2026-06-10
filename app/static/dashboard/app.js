// Global State
let prevStrategies = {};
let isBotRunning = false;
let selectedDate = '';

// DOM elements
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const dailyPnlEl = document.getElementById('daily-pnl');
const dailyPnlSubtext = document.getElementById('daily-pnl-subtext');
const accumulatedPnlEl = document.getElementById('accumulated-pnl');
const strategyModeEl = document.getElementById('strategy-mode');
const tradeAllowedEl = document.getElementById('trade-allowed-status');
const symbolsGrid = document.getElementById('symbols-grid');
const tradesTbody = document.getElementById('trades-tbody');
const toastContainer = document.getElementById('toast-container');

// Advanced Performance Widget Elements
const widgetTotalProfit = document.getElementById('widget-total-profit');
const widgetWinRate = document.getElementById('widget-win-rate');
const widgetTotalTrades = document.getElementById('widget-total-trades');
const widgetRatio = document.getElementById('widget-ratio');
const widgetDrawdown = document.getElementById('widget-drawdown');

// Filter & Control Elements
const filterDateInput = document.getElementById('filter-date');
const btnClearFilter = document.getElementById('btn-clear-filter');
const btnToggleBot = document.getElementById('btn-toggle-bot');
const btnResetOps = document.getElementById('btn-reset-ops');
const btnLogout = document.getElementById('btn-logout');

// Fetch dashboard metrics from FastAPI API
async function fetchMetrics() {
    try {
        const response = await fetch('/api/v1/dashboard');
        if (response.status === 401) {
            // Redirect to login if unauthorized
            window.location.href = 'login.html';
            return;
        }
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        updateUI(data);
        
        // If a date filter is selected, load filtered trades, otherwise render recent trades from response
        if (selectedDate) {
            fetchFilteredTrades();
        } else {
            renderTrades(data.recent_trades || []);
        }
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        setOfflineUI();
    }
}

// Fetch trades filtered by the selected date
async function fetchFilteredTrades() {
    try {
        const url = `/api/v1/dashboard/trades?date=${selectedDate}`;
        const response = await fetch(url);
        if (response.status === 401) {
            window.location.href = 'login.html';
            return;
        }
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const trades = await response.json();
        renderTrades(trades);
    } catch (error) {
        console.error('Error fetching filtered trades:', error);
        tradesTbody.innerHTML = '<tr><td colspan="7" class="loading-placeholder" style="color: var(--accent-red);">Error al cargar transacciones del día.</td></tr>';
    }
}

// Update DOM elements with API response
function updateUI(data) {
    // 1. System Status & Bot Button Toggle
    isBotRunning = data.bot_running;
    if (isBotRunning) {
        statusIndicator.className = 'status-indicator online';
        statusText.textContent = 'En ejecución (ON)';
        
        btnToggleBot.textContent = 'Detener Bot';
        btnToggleBot.className = 'btn btn-danger';
    } else {
        statusIndicator.className = 'status-indicator';
        statusText.textContent = 'Inactivo (OFF)';
        
        btnToggleBot.textContent = 'Iniciar Bot';
        btnToggleBot.className = 'btn btn-primary';
    }

    // 2. Metrics Cards
    // Daily PnL
    const dailyVal = data.daily_pnl || 0.0;
    dailyPnlEl.textContent = `${dailyVal >= 0 ? '+' : ''}${dailyVal.toFixed(4)}`;
    dailyPnlEl.className = `metric-value ${dailyVal >= 0 ? 'positive' : 'negative'}`;
    
    // Total PnL (Metrics Card)
    const accumVal = data.accumulated_pnl || 0.0;
    accumulatedPnlEl.textContent = `${accumVal >= 0 ? '+' : ''}${accumVal.toFixed(4)}`;
    accumulatedPnlEl.className = `metric-value ${accumVal >= 0 ? 'positive' : 'negative'}`;

    // Strategy Mode & Allowed status
    strategyModeEl.textContent = data.strategy_mode || 'Auto';
    if (data.allowed_to_trade) {
        tradeAllowedEl.textContent = 'Operaciones permitidas';
        tradeAllowedEl.style.color = 'var(--accent-green)';
    } else {
        tradeAllowedEl.textContent = 'Operaciones bloqueadas (Max Drawdown)';
        tradeAllowedEl.style.color = 'var(--accent-red)';
    }

    // 3. Render Advanced Performance Widget
    const perf = data.performance_stats || {};
    const totalProfit = perf.total_profit || 0.0;
    widgetTotalProfit.textContent = `${totalProfit >= 0 ? '+' : ''}$${totalProfit.toFixed(4)}`;
    widgetTotalProfit.className = `stat-value ${totalProfit >= 0 ? 'positive' : 'negative'}`;
    
    widgetWinRate.textContent = `${(perf.win_rate || 0.0).toFixed(1)}%`;
    widgetTotalTrades.textContent = perf.total_trades || 0;
    widgetRatio.textContent = `${perf.winning_trades || 0} / ${perf.losing_trades || 0}`;
    
    const dd = perf.max_drawdown || 0.0;
    widgetDrawdown.textContent = `$${dd.toFixed(4)}`;
    widgetDrawdown.className = `stat-value ${dd > 0 ? 'negative' : ''}`;

    // 4. Render Symbols Grid & Track Strategy changes
    symbolsGrid.innerHTML = '';
    const symbols = Object.keys(data.symbol_regimes || {});
    
    if (symbols.length === 0) {
        symbolsGrid.innerHTML = '<div class="loading-placeholder">Sin pares configurados en .env</div>';
    } else {
        symbols.forEach(symbol => {
            const regime = (data.symbol_regimes[symbol] || 'Unknown').toLowerCase();
            const strategyName = data.symbol_strategies[symbol] || 'RSIStrategy';
            
            // Check if strategy changed for this symbol to trigger a toast
            if (prevStrategies[symbol] && prevStrategies[symbol] !== strategyName) {
                showToast(
                    `Estrategia Actualizada: ${symbol}`,
                    `Cambió de ${prevStrategies[symbol]} a ${strategyName} debido al régimen de mercado.`
                );
            }
            // Save to state
            prevStrategies[symbol] = strategyName;
            
            const card = document.createElement('div');
            card.className = 'symbol-card';
            card.innerHTML = `
                <div class="symbol-header">
                    <span class="symbol-name">${symbol}</span>
                    <span class="regime-tag ${regime}">${data.symbol_regimes[symbol]}</span>
                </div>
                <div class="strategy-info">
                    <span class="strategy-label">Estrategia Activa</span>
                    <span class="strategy-value">${strategyName}</span>
                </div>
            `;
            symbolsGrid.appendChild(card);
        });
    }
}

// Render Trades List inside the Table
function renderTrades(trades) {
    tradesTbody.innerHTML = '';
    
    if (trades.length === 0) {
        const msg = selectedDate 
            ? `No se han registrado operaciones el día ${selectedDate}.`
            : "No se han registrado operaciones en SQLite aún.";
        tradesTbody.innerHTML = `<tr><td colspan="7" class="loading-placeholder">${msg}</td></tr>`;
    } else {
        trades.forEach(trade => {
            const row = document.createElement('tr');
            
            // Format timestamp (ISO to local date-time)
            let dateStr = 'N/A';
            if (trade.timestamp) {
                const isoStr = trade.timestamp.includes(' ') ? trade.timestamp.replace(' ', 'T') : trade.timestamp;
                const d = new Date(isoStr + 'Z');
                dateStr = isNaN(d.getTime()) ? trade.timestamp : d.toLocaleString();
            }

            const rsiVal = trade.rsi !== null && trade.rsi !== undefined ? parseFloat(trade.rsi).toFixed(2) : '-';
            const side = (trade.side || 'BUY').toUpperCase();
            
            row.innerHTML = `
                <td>${dateStr}</td>
                <td>${trade.order_id}</td>
                <td style="font-weight: 600;">${trade.symbol}</td>
                <td><span class="side-badge ${side.toLowerCase()}">${side}</span></td>
                <td>${parseFloat(trade.price).toFixed(4)}</td>
                <td>${parseFloat(trade.quantity).toFixed(6)}</td>
                <td style="font-weight: 600;">${rsiVal}</td>
            `;
            tradesTbody.appendChild(row);
        });
    }
}

// Fallback visual state when the server cannot be reached
function setOfflineUI() {
    statusIndicator.className = 'status-indicator offline';
    statusText.textContent = 'Error de conexión';
    tradeAllowedEl.textContent = 'Sin respuesta del bot';
    tradeAllowedEl.style.color = 'var(--accent-red)';
}

// Show animated Toast notifications for strategy switching
function showToast(title, message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
        <div class="toast-header">
            <span>${title}</span>
            <span style="font-size: 0.75rem; cursor: pointer;" onclick="this.parentElement.parentElement.remove()">✕</span>
        </div>
        <div class="toast-body">${message}</div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto-remove toast after 6 seconds
    setTimeout(() => {
        toast.classList.add('fade-out');
        toast.addEventListener('animationend', () => {
            toast.remove();
        });
    }, 6000);
}

// --- Event Handlers & Control Triggers ---

// Listen for Date Filter changes
filterDateInput.addEventListener('change', (e) => {
    selectedDate = e.target.value;
    if (selectedDate) {
        fetchFilteredTrades();
    } else {
        fetchMetrics();
    }
});

// Clear Date Filter
btnClearFilter.addEventListener('click', () => {
    filterDateInput.value = '';
    selectedDate = '';
    fetchMetrics();
});

// Start or Stop Bot Execution
btnToggleBot.addEventListener('click', async () => {
    const action = isBotRunning ? 'stop' : 'start';
    const actionSpanish = isBotRunning ? 'DETENER' : 'INICIAR';
    
    if (!confirm(`¿Estás seguro de que deseas ${actionSpanish} el bot de trading?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/dashboard/bot/${action}`, { method: 'POST' });
        if (response.ok) {
            showToast(`Bot Actualizado`, `Se ejecutó el comando para ${actionSpanish} el bot.`);
            fetchMetrics();
        } else {
            alert('Error al enviar comando al bot.');
        }
    } catch (e) {
        alert('Error de red al intentar contactar al bot.');
    }
});

// Reset Operations and metrics
btnResetOps.addEventListener('click', async () => {
    if (!confirm('🚨 ¡ATENCIÓN! ¿Estás seguro de que deseas REINICIAR todas las estadísticas, PnL diario y limpiar el estado de posiciones abiertas? Esto no cerrará las órdenes en Binance.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/v1/dashboard/reset-operations', { method: 'POST' });
        if (response.ok) {
            showToast('Operaciones Reiniciadas', 'Las métricas, posiciones abiertas y PnL se han limpiado.');
            fetchMetrics();
        } else {
            alert('Error al reiniciar operaciones.');
        }
    } catch (e) {
        alert('Error de red al intentar reiniciar operaciones.');
    }
});

// Logout flow
btnLogout.addEventListener('click', async () => {
    if (!confirm('¿Deseas cerrar tu sesión?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/v1/dashboard/logout', { method: 'POST' });
        if (response.ok) {
            window.location.href = 'login.html';
        }
    } catch (e) {
        window.location.href = 'login.html'; // Force redirect
    }
});

// Initial fetch and start polling interval
fetchMetrics();
setInterval(fetchMetrics, 10000);
