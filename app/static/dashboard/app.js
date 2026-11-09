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

    // 5. Render Local AI & Microstructure Analytics
    renderMLInsights(data.ml_insights || {});
}

function renderMLInsights(ml) {
    const modelsCountEl = document.getElementById('ai-models-count');
    const cvAccEl = document.getElementById('ai-cv-accuracy');
    const liveAccEl = document.getElementById('ai-live-accuracy');
    const liveEvalSubEl = document.getElementById('ai-live-evaluated-sub');
    const vetoesCountEl = document.getElementById('ai-vetoes-count');
    const vetoesSavedSubEl = document.getElementById('ai-vetoes-saved-sub');
    const aiSymbolsGrid = document.getElementById('ai-symbols-grid');
    const aiDecisionsTbody = document.getElementById('ai-decisions-tbody');
    const aiBadge = document.getElementById('ai-engine-badge');

    if (!modelsCountEl || !aiSymbolsGrid) return;

    if (aiBadge) {
        aiBadge.textContent = ml.enabled ? 'ENSEMBLE ACTIVO' : 'MODO PASIVO';
        aiBadge.className = `regime-tag ${ml.enabled ? 'trending' : 'ranging'}`;
    }

    modelsCountEl.textContent = `${ml.models_active || 0} Pares`;
    cvAccEl.textContent = `${(ml.avg_cv_accuracy || 0).toFixed(1)}%`;

    if (ml.live_accuracy_pct !== null && ml.live_accuracy_pct !== undefined) {
        liveAccEl.textContent = `${ml.live_accuracy_pct.toFixed(1)}%`;
        liveAccEl.className = `stat-value ${ml.live_accuracy_pct >= 50 ? 'positive' : 'negative'}`;
        liveEvalSubEl.textContent = `${ml.live_correct_total || 0} aciertos de ${ml.live_evaluated_total || 0} verificadas`;
    } else {
        liveAccEl.textContent = 'En observación';
        liveAccEl.className = 'stat-value';
        liveEvalSubEl.textContent = 'Verificando barreras en próximas velas 1m...';
    }

    vetoesCountEl.textContent = ml.vetoes_total || 0;
    vetoesSavedSubEl.textContent = `${ml.vetoes_saved || 0} caídas evitadas con éxito`;

    // Render per-symbol AI cards
    const symMap = ml.symbols || {};
    const symKeys = Object.keys(symMap);
    aiSymbolsGrid.innerHTML = '';

    if (symKeys.length === 0) {
        aiSymbolsGrid.innerHTML = '<div class="loading-placeholder">Entrenando modelos locales...</div>';
    } else {
        symKeys.forEach(sym => {
            const s = symMap[sym];
            const sig = (s.latest_signal || 'HOLD').toUpperCase();
            const sigBadgeClass = sig === 'BUY' ? 'buy' : (sig === 'SELL' ? 'sell' : 'unknown');
            const buyProb = s.buy_prob || 0;
            const sellProb = s.sell_prob || 0;
            const obi = s.obi || 0;
            const obiColor = obi > 0.15 ? 'var(--accent-green)' : (obi < -0.15 ? 'var(--accent-red)' : 'var(--text-secondary)');
            const obiLabel = obi > 0.25 ? 'Fuerte Compra' : (obi < -0.35 ? 'Muro de Venta (Veto)' : 'Equilibrado');
            const liveText = s.live_evaluated > 0
                ? `${s.live_accuracy.toFixed(1)}% (${s.live_correct}/${s.live_evaluated})`
                : `CV: ${s.cv_accuracy.toFixed(1)}%`;

            const card = document.createElement('div');
            card.className = 'symbol-card';
            card.innerHTML = `
                <div class="symbol-header">
                    <span class="symbol-name">${sym}</span>
                    <span class="side-badge ${sigBadgeClass}">${sig} (${(s.latest_confidence || 0).toFixed(0)}%)</span>
                </div>
                <div style="display: flex; flex-direction: column; gap: 0.45rem; font-size: 0.8rem;">
                    <div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.2rem;">
                            <span style="color: var(--accent-green); font-weight: 600;">P(Take Profit): ${buyProb.toFixed(1)}%</span>
                            <span style="color: var(--accent-red); font-weight: 600;">P(Stop Loss): ${sellProb.toFixed(1)}%</span>
                        </div>
                        <div style="display: flex; height: 7px; border-radius: 4px; overflow: hidden; background: rgba(255,255,255,0.08);">
                            <div style="width: ${Math.min(100, buyProb)}%; background: var(--accent-green);"></div>
                            <div style="width: ${Math.max(0, 100 - buyProb - sellProb)}%; background: rgba(156,163,175,0.35);"></div>
                            <div style="width: ${Math.min(100, sellProb)}%; background: var(--accent-red);"></div>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding-top: 0.25rem; border-top: 1px solid rgba(255,255,255,0.04);">
                        <span class="strategy-label">Order Book (OBI):</span>
                        <span style="font-weight: 600; color: ${obiColor};">${obi >= 0 ? '+' : ''}${obi.toFixed(2)} (${obiLabel})</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span class="strategy-label">Precisión Acierto:</span>
                        <span style="font-weight: 600; color: #e5e7eb;">${liveText}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span class="strategy-label">Muestras / Mecha Compra:</span>
                        <span style="color: var(--text-secondary);">${s.n_samples || 0} velas | ${Math.min(100, Math.max(0, (s.buying_pressure_wick > 100 ? s.buying_pressure_wick / 100 : (s.buying_pressure_wick || 50)))).toFixed(0)}%</span>
                    </div>
                </div>
            `;
            aiSymbolsGrid.appendChild(card);
        });
    }

    // Render recent AI decisions audit table
    if (aiDecisionsTbody) {
        const decisions = ml.recent_decisions || [];
        aiDecisionsTbody.innerHTML = '';
        if (decisions.length === 0) {
            aiDecisionsTbody.innerHTML = '<tr><td colspan="7" class="loading-placeholder">Esperando el próximo cierre de vela de 1m para registrar decisiones...</td></tr>';
        } else {
            decisions.forEach(d => {
                const sig = (d.signal || 'HOLD').toUpperCase();
                const sigBadgeClass = sig === 'BUY' ? 'buy' : (sig === 'SELL' ? 'sell' : 'unknown');
                let verdictHtml = '<span style="color: var(--accent-yellow); font-weight: 600;">⏳ Evaluando barreras...</span>';
                if (d.verified) {
                    if (d.is_correct) {
                        verdictHtml = `<span style="color: var(--accent-green); font-weight: 700;">✅ ACERTÓ (${d.actual_outcome})</span>`;
                    } else {
                        verdictHtml = `<span style="color: var(--accent-red); font-weight: 700;">❌ FALLÓ (${d.actual_outcome})</span>`;
                    }
                }
                const obiVal = d.obi || 0;
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${d.time || '-'}</td>
                    <td style="font-weight: 700;">${d.symbol}</td>
                    <td>$${parseFloat(d.price || 0).toFixed(4)}</td>
                    <td><span class="side-badge ${sigBadgeClass}">${sig} (${(d.confidence || 0).toFixed(0)}%)</span></td>
                    <td>
                        <span style="color: var(--accent-green); font-weight: 600;">TP: ${(d.buy_prob || 0).toFixed(1)}%</span>
                        <span style="color: var(--text-secondary); margin: 0 0.35rem;">|</span>
                        <span style="color: var(--accent-red); font-weight: 600;">SL: ${(d.sell_prob || 0).toFixed(1)}%</span>
                    </td>
                    <td style="color: ${obiVal >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'}; font-weight: 600;">${obiVal >= 0 ? '+' : ''}${obiVal.toFixed(2)}</td>
                    <td>${verdictHtml}</td>
                `;
                aiDecisionsTbody.appendChild(row);
            });
        }
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

// --- Historical Chart State & Logic ---
let chartInstance = null;
let currentChartSymbol = 'BTCUSDC';
let currentChartInterval = '1h';
let currentChartType = 'area'; // 'area' or 'candlestick'

// DOM elements for Chart
const chartSymbolSearch = document.getElementById('chart-symbol-search');
const chartIntervalSelect = document.getElementById('chart-interval-select');
const btnChartArea = document.getElementById('btn-chart-area');
const btnChartCandle = document.getElementById('btn-chart-candle');
const chartLoadingOverlay = document.getElementById('chart-loading-overlay');

// Fetch historical price klines
async function fetchHistoricalData(symbol, interval) {
    if (!chartLoadingOverlay) return;
    chartLoadingOverlay.classList.add('active');
    try {
        const response = await fetch(`/api/v1/dashboard/historical?symbol=${symbol}&interval=${interval}&limit=120`);
        if (response.status === 401) {
            window.location.href = 'login.html';
            return;
        }
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        renderHistoricalChart(data, currentChartType);
    } catch (error) {
        console.error('Error fetching historical chart data:', error);
        showToast('Error de Carga', `No se pudo obtener el historial para ${symbol}. Verifique el símbolo.`);
    } finally {
        chartLoadingOverlay.classList.remove('active');
    }
}

// Render or update ApexCharts widget
function renderHistoricalChart(data, type) {
    const chartData = data.map(d => {
        if (type === 'candlestick') {
            return {
                x: new Date(d.time),
                y: [d.open, d.high, d.low, d.close]
            };
        } else {
            return {
                x: new Date(d.time),
                y: d.close
            };
        }
    });

    const options = {
        series: [{
            name: type === 'candlestick' ? 'Vela' : 'Precio de Cierre',
            data: chartData
        }],
        chart: {
            type: type,
            height: 350,
            background: 'transparent',
            toolbar: {
                show: true,
                tools: {
                    download: false,
                    selection: true,
                    zoom: true,
                    zoomin: true,
                    zoomout: true,
                    pan: true,
                    reset: true
                }
            },
            foreColor: '#9ca3af'
        },
        theme: {
            mode: 'dark'
        },
        grid: {
            borderColor: 'rgba(255, 255, 255, 0.05)',
            xaxis: {
                lines: { show: false }
            },
            yaxis: {
                lines: { show: true }
            }
        },
        stroke: {
            curve: 'smooth',
            width: type === 'candlestick' ? 1 : 3,
            colors: type === 'candlestick' ? undefined : ['#8b5cf6']
        },
        fill: {
            type: type === 'candlestick' ? 'solid' : 'gradient',
            gradient: {
                shadeIntensity: 1,
                opacityFrom: 0.4,
                opacityTo: 0.0,
                stops: [0, 90, 100],
                colorStops: [
                    {
                        offset: 0,
                        color: '#8b5cf6',
                        opacity: 0.35
                    },
                    {
                        offset: 100,
                        color: '#3b82f6',
                        opacity: 0.0
                    }
                ]
            }
        },
        xaxis: {
            type: 'datetime',
            axisBorder: { show: false },
            axisTicks: { show: false },
            labels: { datetimeUTC: false }
        },
        yaxis: {
            labels: {
                formatter: function (val) {
                    return val >= 1000 ? val.toLocaleString(undefined, { maximumFractionDigits: 0 }) : val.toFixed(4);
                }
            }
        },
        tooltip: {
            theme: 'dark',
            x: { format: 'dd MMM yyyy HH:mm' }
        },
        colors: ['#8b5cf6', '#3b82f6', '#10b981', '#ef4444']
    };

    if (chartInstance) {
        chartInstance.destroy(); // Clear existing instance to prevent merging bugs
    }
    chartInstance = new ApexCharts(document.querySelector("#historical-chart"), options);
    chartInstance.render();
}

// Chart Event Listeners
chartSymbolSearch.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const symbol = chartSymbolSearch.value.trim().toUpperCase();
        if (symbol) {
            currentChartSymbol = symbol;
            fetchHistoricalData(currentChartSymbol, currentChartInterval);
        }
    }
});

chartIntervalSelect.addEventListener('change', (e) => {
    currentChartInterval = e.target.value;
    fetchHistoricalData(currentChartSymbol, currentChartInterval);
});

btnChartArea.addEventListener('click', () => {
    if (currentChartType !== 'area') {
        currentChartType = 'area';
        btnChartArea.classList.add('active');
        btnChartCandle.classList.remove('active');
        fetchHistoricalData(currentChartSymbol, currentChartInterval);
    }
});

btnChartCandle.addEventListener('click', () => {
    if (currentChartType !== 'candlestick') {
        currentChartType = 'candlestick';
        btnChartCandle.classList.add('active');
        btnChartArea.classList.remove('active');
        fetchHistoricalData(currentChartSymbol, currentChartInterval);
    }
});

// Initial fetch and start polling interval
fetchMetrics();
setInterval(fetchMetrics, 10000);

// Initial historical chart load
fetchHistoricalData(currentChartSymbol, currentChartInterval);
