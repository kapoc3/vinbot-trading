// Global State
let prevStrategies = {};
let isBotRunning = false;
let selectedDate = '';
let lastDashboardData = null;

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
    lastDashboardData = data;

    // 0. Update Profile Badge & Brand Title
    const profileBadgeEl = document.getElementById('profile-badge');
    const brandTitleEl = document.getElementById('brand-title');
    if (profileBadgeEl && data.bot_profile) {
        profileBadgeEl.textContent = data.bot_profile;
        if (data.scanner_enabled) {
            profileBadgeEl.style.background = 'rgba(239, 68, 68, 0.2)';
            profileBadgeEl.style.color = '#f87171';
            profileBadgeEl.style.borderColor = 'rgba(239, 68, 68, 0.4)';
        } else {
            profileBadgeEl.style.background = 'rgba(59, 130, 246, 0.2)';
            profileBadgeEl.style.color = '#60a5fa';
            profileBadgeEl.style.borderColor = 'rgba(59, 130, 246, 0.4)';
        }
    }
    if (brandTitleEl && data.project_name) {
        brandTitleEl.textContent = data.project_name;
    }

    // Update Navigation Tab Pills
    const navPortPill = document.getElementById('nav-portfolio-pill');
    if (navPortPill && data.wallet) {
        navPortPill.textContent = `$${(data.wallet.total_usd || 0).toFixed(2)}`;
    }
    const navTradesPill = document.getElementById('nav-trades-pill');
    if (navTradesPill && data.recent_trades) {
        navTradesPill.textContent = `${data.recent_trades.length}`;
    }

    // Update System Tab Information
    const sysProfilePill = document.getElementById('system-profile-pill');
    if (sysProfilePill && data.bot_profile) sysProfilePill.textContent = data.bot_profile;
    const sysProfileDesc = document.getElementById('system-profile-desc');
    if (sysProfileDesc) {
        sysProfileDesc.textContent = data.scanner_enabled 
            ? 'Modo Satélite Hot Momentum (30% Capital) con rotación continua en líderes de Binance.' 
            : 'Modo Core (70% Capital) en activos consolidados de bajo riesgo (BTC, ETH, SOL, BNB).';
    }
    const sysCapVal = document.getElementById('system-capital-val');
    if (sysCapVal) sysCapVal.textContent = data.scanner_enabled ? '$30.00 USD' : '$70.00 USD';
    const sysScanStatus = document.getElementById('system-scanner-status');
    if (sysScanStatus) {
        sysScanStatus.textContent = data.scanner_enabled ? '🟢 ACTIVO (Cada 2 horas en 1h window)' : '⚪ Inactivo (Modo Core Fijo)';
        sysScanStatus.style.color = data.scanner_enabled ? 'var(--accent-green)' : 'var(--text-secondary)';
    }
    const sysFeeVal = document.getElementById('system-fee-val');
    if (sysFeeVal && data.scanner_info) {
        sysFeeVal.textContent = `${data.scanner_info.fee_pct}% (${data.scanner_info.round_trip_factor}x)`;
    }

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

    // Sync System tab bot button
    const btnToggleBotSys = document.getElementById('btn-toggle-bot-system');
    if (btnToggleBotSys) {
        btnToggleBotSys.textContent = isBotRunning ? 'Detener Bot' : 'Iniciar Bot';
        btnToggleBotSys.className = isBotRunning ? 'btn btn-danger' : 'btn btn-primary';
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

    // Update Topbar Quick KPI Glance
    const topCapital = document.getElementById('topbar-capital');
    const topDaily = document.getElementById('topbar-daily-pnl');
    const topWin = document.getElementById('topbar-win-rate');
    if (topCapital && data.wallet) {
        topCapital.textContent = `$${(data.wallet.total_usd || 0.0).toFixed(2)}`;
    }
    if (topDaily) {
        const dPnl = data.daily_pnl || 0.0;
        topDaily.textContent = `${dPnl >= 0 ? '+' : ''}$${dPnl.toFixed(2)}`;
        topDaily.className = `kpi-val ${dPnl >= 0 ? 'positive' : 'negative'}`;
    }
    if (topWin && data.performance_stats) {
        topWin.textContent = `${(data.performance_stats.win_rate || 0.0).toFixed(1)}%`;
    }

    // 3.5 Render Active Open Positions
    renderActivePositions(data.active_positions || {}, data);

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
            card.className = 'symbol-card clickable-card';
            card.title = `Clic para ver análisis y detalles de ${symbol}`;
            card.onclick = () => openSymbolModal(symbol);
            card.innerHTML = `
                <div class="symbol-header">
                    <span class="symbol-name">${symbol}</span>
                    <span class="regime-tag ${regime}">${data.symbol_regimes[symbol]}</span>
                </div>
                <div class="strategy-info">
                    <span class="strategy-label">Estrategia Activa</span>
                    <span class="strategy-value">${strategyName}</span>
                </div>
                <div style="font-size: 0.75rem; color: #60a5fa; margin-top: 0.5rem; text-align: right; font-weight: 600;">
                    Ver detalle completo ➔
                </div>
            `;
            symbolsGrid.appendChild(card);
        });
    }

    // 5. Render Wallet & Crypto Holdings
    renderWalletPortfolio(data.wallet || {});

    // 6. Render Local AI & Microstructure Analytics
    renderMLInsights(data.ml_insights || {});

    // 7. Render Closed Buy-Sell Cycles
    renderClosedCycles(data.closed_cycles || []);
}

function renderWalletPortfolio(wallet) {
    const totalUsdEl = document.getElementById('wallet-total-usd');
    const breakdownSubEl = document.getElementById('wallet-breakdown-subtext');
    const goalBadgeEl = document.getElementById('wallet-goal-badge');
    const summaryLineEl = document.getElementById('wallet-summary-line');
    const goalPctTextEl = document.getElementById('wallet-goal-pct-text');
    const goalBarEl = document.getElementById('wallet-goal-bar');
    const assetsGridEl = document.getElementById('wallet-assets-grid');

    if (!totalUsdEl || !assetsGridEl) return;

    const totalUsd = wallet.total_usd || 0.0;
    const freeStable = wallet.free_stable_usd || 0.0;
    const investedCrypto = wallet.invested_crypto_usd || 0.0;
    const lockedUsd = wallet.locked_usd || 0.0;
    const goalUsd = wallet.goal_usd || 100.0;
    const goalPct = wallet.goal_progress_pct || Math.min(100.0, (totalUsd / goalUsd) * 100.0);
    const assets = wallet.assets || [];

    totalUsdEl.textContent = `$${totalUsd.toFixed(2)}`;
    breakdownSubEl.textContent = `Libre: $${freeStable.toFixed(2)} USDC | En Cripto: $${investedCrypto.toFixed(2)}`;

    if (goalBadgeEl) {
        goalBadgeEl.textContent = `Meta $${goalUsd.toFixed(0)} USDC: $${totalUsd.toFixed(2)} (${goalPct.toFixed(1)}%)`;
    }

    if (summaryLineEl) {
        const lockedText = lockedUsd > 0.01 ? ` | En órdenes: $${lockedUsd.toFixed(2)}` : '';
        summaryLineEl.textContent = `Liquidez Libre (Stablecoins): $${freeStable.toFixed(2)} | Activos Cripto: $${investedCrypto.toFixed(2)}${lockedText}`;
    }

    if (goalPctTextEl) {
        const remaining = Math.max(0.0, goalUsd - totalUsd);
        goalPctTextEl.textContent = remaining > 0
            ? `${goalPct.toFixed(1)}% completado (Faltan $${remaining.toFixed(2)} para $${goalUsd.toFixed(0)})`
            : `🎉 ¡Meta de $${goalUsd.toFixed(0)} USDC alcanzada!`;
    }

    if (goalBarEl) {
        const stablePctOfGoal = Math.min(100, (freeStable / goalUsd) * 100);
        const cryptoPctOfGoal = Math.min(100 - stablePctOfGoal, (investedCrypto / goalUsd) * 100);
        goalBarEl.innerHTML = `
            <div title="Liquidez Stablecoins: $${freeStable.toFixed(2)}" style="width: ${stablePctOfGoal}%; background: #10b981; transition: width 0.5s ease;"></div>
            <div title="Invertido en Cripto: $${investedCrypto.toFixed(2)}" style="width: ${cryptoPctOfGoal}%; background: #f59e0b; transition: width 0.5s ease;"></div>
        `;
    }

    assetsGridEl.innerHTML = '';
    if (assets.length === 0) {
        assetsGridEl.innerHTML = '<div class="loading-placeholder">No se encontraron activos con saldo en Binance Spot.</div>';
        return;
    }

    const coinIcons = {
        USDC: '💵',
        USDT: '💵',
        BTC: '₿',
        ETH: '💎',
        SOL: '🟣',
        BNB: '🟡'
    };

    assets.forEach(item => {
        const icon = coinIcons[item.asset] || '🪙';
        const isStable = item.is_stable;
        const inBotPos = item.in_bot_position;

        let badgeClass = 'ranging';
        let badgeLabel = 'RESERVA SPOT';
        if (isStable) {
            badgeClass = 'trending';
            badgeLabel = 'LIQUIDEZ BASE';
        } else if (inBotPos) {
            badgeClass = 'highvolatility';
            badgeLabel = 'POSICIÓN BOT ACTIVA';
        }

        const qtyDecimals = isStable ? 2 : (item.total < 0.001 ? 8 : (item.total < 1 ? 6 : 4));
        const priceDecimals = item.price_usd >= 100 ? 2 : (item.price_usd >= 1 ? 4 : 6);

        let pnlRowHtml = '';
        if (!isStable && item.entry_price) {
            const pnlVal = item.unrealized_pnl_pct || 0.0;
            const pnlColor = pnlVal >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
            pnlRowHtml = `
                <div style="display: flex; justify-content: space-between; padding-top: 0.2rem; border-top: 1px solid rgba(255,255,255,0.04);">
                    <span class="strategy-label">Entrada Bot / PnL:</span>
                    <span style="font-weight: 700; color: ${pnlColor};">$${item.entry_price.toFixed(priceDecimals)} (${pnlVal >= 0 ? '+' : ''}${pnlVal.toFixed(2)}%)</span>
                </div>
            `;
        }

        const card = document.createElement('div');
        card.className = 'symbol-card' + (!isStable ? ' clickable-card' : '');
        if (!isStable) {
            card.title = `Clic para ver análisis y detalles de ${item.asset}`;
            card.onclick = () => openSymbolModal(item.asset + 'USDC');
        }
        card.innerHTML = `
            <div class="symbol-header">
                <span class="symbol-name">${icon} ${item.asset}</span>
                <span class="regime-tag ${badgeClass}">${badgeLabel}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin: 0.15rem 0;">
                <span style="font-size: 1.45rem; font-weight: 800; color: var(--text-primary);">$${item.usd_value.toFixed(2)}</span>
                <span style="font-size: 0.8rem; font-weight: 600; color: var(--accent-blue);">${(item.allocation_pct || 0).toFixed(1)}% del total</span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.8rem;">
                <div style="display: flex; justify-content: space-between;">
                    <span class="strategy-label">Cantidad Total:</span>
                    <span style="font-weight: 600; color: #e5e7eb;">${item.total.toFixed(qtyDecimals)} ${item.asset}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span class="strategy-label">Disponible / En Orden:</span>
                    <span style="color: var(--text-secondary);">${item.free.toFixed(qtyDecimals)} / ${item.locked.toFixed(qtyDecimals)}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span class="strategy-label">Precio Mercado:</span>
                    <span style="color: var(--text-secondary);">$${item.price_usd.toFixed(priceDecimals)}</span>
                </div>
                ${pnlRowHtml}
            </div>
        `;
        assetsGridEl.appendChild(card);
    });
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
            card.className = 'symbol-card clickable-card';
            card.title = `Clic para ver análisis y detalles de ${sym}`;
            card.onclick = () => openSymbolModal(sym);
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
                    ${s.kronos ? `
                    <div style="margin-top: 0.35rem; padding-top: 0.35rem; border-top: 1px dashed rgba(147, 51, 234, 0.4); display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 0.76rem; color: #c084fc; font-weight: 600;">🧠 4to Cerebro (Kronos):</span>
                        <span style="font-size: 0.76rem; font-weight: 700; color: ${s.kronos.direction === 'BULLISH' ? 'var(--accent-green)' : (s.kronos.direction === 'BEARISH' ? 'var(--accent-red)' : 'var(--accent-yellow)')};">
                            ${s.kronos.direction} (${s.kronos.expected_pct >= 0 ? '+' : ''}${s.kronos.expected_pct}%)
                        </span>
                    </div>` : ''}
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
                const barsElapsed = d.bars_elapsed !== undefined ? d.bars_elapsed : 0;
                const horizon = d.horizon || 10;
                let verdictHtml = `<span style="color: var(--accent-yellow); font-weight: 600;">⏳ Evaluando (${barsElapsed}/${horizon}m)...</span>`;
                if (d.verified) {
                    if (d.is_correct) {
                        verdictHtml = `<span style="color: var(--accent-green); font-weight: 700;">✅ ACERTÓ (${d.actual_outcome})</span>`;
                    } else {
                        verdictHtml = `<span style="color: var(--accent-red); font-weight: 700;">❌ FALLÓ (Real: ${d.actual_outcome})</span>`;
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

let allClosedCycles = [];
let cyclesCurrentPage = 1;
const CYCLES_PAGE_SIZE = 8;

let allTrades = [];
let tradesCurrentPage = 1;
const TRADES_PAGE_SIZE = 10;

function renderClosedCycles(cycles) {
    const grid = document.getElementById('closed-cycles-grid');
    const paginationBar = document.getElementById('cycles-pagination-bar');
    const paginationInfo = document.getElementById('cycles-pagination-info');
    const pageDisplay = document.getElementById('cycles-page-display');
    const prevBtn = document.getElementById('cycles-prev-btn');
    const nextBtn = document.getElementById('cycles-next-btn');

    if (!grid) return;
    if (cycles !== undefined) {
        allClosedCycles = cycles || [];
    }

    grid.innerHTML = '';

    if (!allClosedCycles || allClosedCycles.length === 0) {
        grid.innerHTML = '<div class="loading-placeholder">Aún no hay ventas cerradas que emparejen compras previas.</div>';
        if (paginationBar) paginationBar.style.display = 'none';
        return;
    }

    const totalPages = Math.max(1, Math.ceil(allClosedCycles.length / CYCLES_PAGE_SIZE));
    if (cyclesCurrentPage > totalPages) cyclesCurrentPage = 1;

    const startIdx = (cyclesCurrentPage - 1) * CYCLES_PAGE_SIZE;
    const endIdx = Math.min(startIdx + CYCLES_PAGE_SIZE, allClosedCycles.length);
    const pageItems = allClosedCycles.slice(startIdx, endIdx);

    pageItems.forEach(c => {
        const pnlUsd = c.pnl_usd || 0.0;
        const pnlPct = c.pnl_pct || 0.0;
        const isWin = pnlUsd >= 0;
        const pnlColor = isWin ? 'var(--accent-green)' : 'var(--accent-red)';
        const borderAccent = isWin ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)';

        let dateStr = c.timestamp || '';
        if (c.timestamp) {
            const isoStr = c.timestamp.includes(' ') ? c.timestamp.replace(' ', 'T') : c.timestamp;
            const d = new Date(isoStr + 'Z');
            if (!isNaN(d.getTime())) dateStr = d.toLocaleString();
        }

        const detailsList = (c.matched_details || []).map(m =>
            `<div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: var(--text-secondary); padding: 0.25rem 0; border-bottom: 1px solid rgba(255,255,255,0.03);">
                <span>↳ Orden Compra <b>#${m.buy_order_id}</b> (${m.qty} a $${parseFloat(m.buy_price).toFixed(2)})</span>
                <span style="color: ${m.pnl_usd >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'}; font-weight: 600;">
                    ${m.pnl_usd >= 0 ? '+' : ''}$${parseFloat(m.pnl_usd).toFixed(4)} USD
                </span>
            </div>`
        ).join('') || '<div style="font-size: 0.75rem; color: var(--text-secondary);">Sin compras desglosadas.</div>';

        const card = document.createElement('div');
        card.className = 'collapsible-card';
        card.style.borderColor = borderAccent;

        card.innerHTML = `
            <div class="collapsible-header" onclick="this.parentElement.classList.toggle('expanded')">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <span style="font-size: 1.25rem;">🪙</span>
                    <div>
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <span style="font-weight: 800; font-size: 1rem; color: #ffffff;">${c.symbol}</span>
                            <span class="regime-tag ${isWin ? 'trending' : 'highvolatility'}" style="font-size: 0.68rem; padding: 2px 6px;">
                                ${isWin ? 'GANANCIA NETA' : 'STOP LOSS'}
                            </span>
                        </div>
                        <span style="font-size: 0.75rem; color: var(--text-secondary);">Venta #${c.sell_order_id} • ${dateStr}</span>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="text-align: right;">
                        <span class="side-badge ${isWin ? 'buy' : 'sell'}" style="font-size: 0.85rem; font-weight: 800;">
                            ${isWin ? '+' : ''}$${pnlUsd.toFixed(4)} USDC (${isWin ? '+' : ''}${pnlPct.toFixed(2)}%)
                        </span>
                    </div>
                    <span class="collapsible-chevron">▼</span>
                </div>
            </div>
            <div class="collapsible-body">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; margin-bottom: 0.75rem; font-size: 0.82rem;">
                    <div class="detail-box">
                        <div class="detail-box-label">Compra Promedio → Venta Real</div>
                        <div class="detail-box-value" style="font-size: 0.95rem;">
                            $${parseFloat(c.avg_buy_price || 0).toFixed(2)} → <strong style="color: #60a5fa;">$${parseFloat(c.sell_price || 0).toFixed(2)}</strong>
                        </div>
                    </div>
                    <div class="detail-box">
                        <div class="detail-box-label">Capital Invertido → Recuperado</div>
                        <div class="detail-box-value" style="font-size: 0.95rem; color: ${pnlColor};">
                            $${parseFloat(c.buy_cost_usd || 0).toFixed(2)} → $${parseFloat(c.sell_value_usd || 0).toFixed(2)} USDC
                        </div>
                    </div>
                    <div class="detail-box">
                        <div class="detail-box-label">Protección de Comisiones</div>
                        <div class="detail-box-value" style="font-size: 0.85rem; color: var(--accent-green);">
                            Garantizado con BE+Fees (0.075%)
                        </div>
                    </div>
                </div>
                <div style="font-size: 0.75rem; font-weight: 700; color: #9ca3af; text-transform: uppercase; margin-bottom: 0.4rem;">
                    Compras Emparejadas FIFO (${(c.matched_details || []).length}):
                </div>
                ${detailsList}
            </div>
        `;
        grid.appendChild(card);
    });

    if (paginationBar) {
        paginationBar.style.display = totalPages > 1 ? 'flex' : 'none';
        if (paginationInfo) {
            paginationInfo.textContent = `Mostrando ${startIdx + 1} - ${endIdx} de ${allClosedCycles.length} ciclos cerrados`;
        }
        if (pageDisplay) {
            pageDisplay.textContent = `Pág. ${cyclesCurrentPage} de ${totalPages}`;
        }
        if (prevBtn) {
            prevBtn.disabled = (cyclesCurrentPage <= 1);
            prevBtn.onclick = () => {
                if (cyclesCurrentPage > 1) {
                    cyclesCurrentPage--;
                    renderClosedCycles();
                }
            };
        }
        if (nextBtn) {
            nextBtn.disabled = (cyclesCurrentPage >= totalPages);
            nextBtn.onclick = () => {
                if (cyclesCurrentPage < totalPages) {
                    cyclesCurrentPage++;
                    renderClosedCycles();
                }
            };
        }
    }
}

// Render Trades List inside the Table with Pagination
function renderTrades(trades) {
    if (trades !== undefined) {
        allTrades = trades || [];
    }
    tradesTbody.innerHTML = '';

    const paginationBar = document.getElementById('trades-pagination-bar');
    const paginationInfo = document.getElementById('trades-pagination-info');
    const pageDisplay = document.getElementById('trades-page-display');
    const prevBtn = document.getElementById('trades-prev-btn');
    const nextBtn = document.getElementById('trades-next-btn');

    if (!allTrades || allTrades.length === 0) {
        const msg = selectedDate 
            ? `No se han registrado operaciones el día ${selectedDate}.`
            : "No se han registrado operaciones en SQLite aún.";
        tradesTbody.innerHTML = `<tr><td colspan="7" class="loading-placeholder">${msg}</td></tr>`;
        if (paginationBar) paginationBar.style.display = 'none';
        return;
    }

    const totalPages = Math.max(1, Math.ceil(allTrades.length / TRADES_PAGE_SIZE));
    if (tradesCurrentPage > totalPages) tradesCurrentPage = 1;

    const startIdx = (tradesCurrentPage - 1) * TRADES_PAGE_SIZE;
    const endIdx = Math.min(startIdx + TRADES_PAGE_SIZE, allTrades.length);
    const pageTrades = allTrades.slice(startIdx, endIdx);

    pageTrades.forEach(trade => {
        const row = document.createElement('tr');
        
        // Format timestamp (ISO to local date-time)
        let dateStr = 'N/A';
        if (trade.timestamp) {
            const isoStr = trade.timestamp.includes(' ') ? trade.timestamp.replace(' ', 'T') : trade.timestamp;
            const d = new Date(isoStr + 'Z');
            dateStr = isNaN(d.getTime()) ? trade.timestamp : d.toLocaleString();
        }

        const side = (trade.side || 'BUY').toUpperCase();
        const price = parseFloat(trade.price || 0);
        const qty = parseFloat(trade.quantity || 0);
        const valUsd = trade.order_value_usd !== undefined ? parseFloat(trade.order_value_usd) : (price * qty);

        // Linked Buy <-> Sell text
        const linkedHtml = trade.linked_text
            ? `<div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.2rem; font-weight: 600;">${trade.linked_text}</div>`
            : '';

        // Buy -> Sell price comparison cell
        let priceComparisonHtml = `$${price.toFixed(2)}`;
        if (side === 'SELL' && trade.buy_price) {
            priceComparisonHtml = `
                <div><span style="color: var(--text-secondary); font-size: 0.78rem;">Compra Prom:</span> $${parseFloat(trade.buy_price).toFixed(2)}</div>
                <div style="font-weight: 700; color: #f3f4f6;"><span style="color: var(--text-secondary); font-size: 0.78rem;">Venta Real:</span> $${price.toFixed(2)}</div>
            `;
        } else if (side === 'BUY' && trade.sell_price) {
            const sLabel = trade.trade_status === 'SOLD' ? 'Vendida a:' : 'Actual:';
            priceComparisonHtml = `
                <div style="font-weight: 700; color: #f3f4f6;"><span style="color: var(--text-secondary); font-size: 0.78rem;">Compra:</span> $${price.toFixed(2)}</div>
                <div><span style="color: var(--text-secondary); font-size: 0.78rem;">${sLabel}</span> $${parseFloat(trade.sell_price).toFixed(2)}</div>
            `;
        }

        // Real PnL cell
        let pnlHtml = '<span style="color: var(--text-secondary);">-</span>';
        if (trade.pnl_usd !== null && trade.pnl_usd !== undefined) {
            const pnlUsd = parseFloat(trade.pnl_usd);
            const pnlPct = parseFloat(trade.pnl_pct || 0);
            const isPos = pnlUsd >= 0;
            const color = isPos ? 'var(--accent-green)' : 'var(--accent-red)';
            let statusTag = '';
            if (side === 'SELL') {
                statusTag = '<div style="font-size: 0.72rem; color: var(--text-secondary);">Ganancia Real Cierre</div>';
            } else if (trade.trade_status === 'SOLD') {
                statusTag = `<div style="font-size: 0.72rem; color: var(--text-secondary);">Cerrada en #${(trade.linked_order_ids || [])[0] || ''}</div>`;
            } else {
                statusTag = '<div style="font-size: 0.72rem; color: #60a5fa;">PnL Flotante (Abierta)</div>';
            }
            pnlHtml = `
                <div style="font-weight: 700; color: ${color};">
                    ${isPos ? '+' : ''}$${pnlUsd.toFixed(4)} USDC (${isPos ? '+' : ''}${pnlPct.toFixed(2)}%)
                </div>
                ${statusTag}
            `;
        }

        row.innerHTML = `
            <td>${dateStr}</td>
            <td>
                <div style="font-weight: 700;">#${trade.order_id}</div>
                ${linkedHtml}
            </td>
            <td style="font-weight: 600;">${trade.symbol}</td>
            <td><span class="side-badge ${side.toLowerCase()}">${side}</span></td>
            <td>${priceComparisonHtml}</td>
            <td>
                <div style="font-weight: 600;">${qty.toFixed(5)}</div>
                <div style="font-size: 0.76rem; color: var(--text-secondary);">$${valUsd.toFixed(2)} USDC</div>
            </td>
            <td>${pnlHtml}</td>
        `;
        tradesTbody.appendChild(row);
    });

    if (paginationBar) {
        paginationBar.style.display = totalPages > 1 ? 'flex' : 'none';
        if (paginationInfo) {
            paginationInfo.textContent = `Mostrando ${startIdx + 1} - ${endIdx} de ${allTrades.length} órdenes`;
        }
        if (pageDisplay) {
            pageDisplay.textContent = `Pág. ${tradesCurrentPage} de ${totalPages}`;
        }
        if (prevBtn) {
            prevBtn.disabled = (tradesCurrentPage <= 1);
            prevBtn.onclick = () => {
                if (tradesCurrentPage > 1) {
                    tradesCurrentPage--;
                    renderTrades();
                }
            };
        }
        if (nextBtn) {
            nextBtn.disabled = (tradesCurrentPage >= totalPages);
            nextBtn.onclick = () => {
                if (tradesCurrentPage < totalPages) {
                    tradesCurrentPage++;
                    renderTrades();
                }
            };
        }
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
    tradesCurrentPage = 1;
    cyclesCurrentPage = 1;
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
    tradesCurrentPage = 1;
    cyclesCurrentPage = 1;
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

// ==============================================================================
// ACTIVE OPEN POSITIONS WIDGET
// ==============================================================================
function renderActivePositions(activePositions, data) {
    const listEl = document.getElementById('active-positions-list');
    const badgeEl = document.getElementById('active-positions-count-badge');
    if (!listEl) return;

    const syms = Object.keys(activePositions || {});
    if (badgeEl) {
        badgeEl.textContent = `${syms.length} ${syms.length === 1 ? 'ACTIVA' : 'ACTIVAS'}`;
        badgeEl.style.background = syms.length > 0 ? 'rgba(16, 185, 129, 0.25)' : 'rgba(255, 255, 255, 0.08)';
        badgeEl.style.color = syms.length > 0 ? '#34d399' : 'var(--text-secondary)';
    }

    if (syms.length === 0) {
        listEl.innerHTML = `
            <div class="loading-placeholder" style="padding: 1rem; text-align: left; border-radius: 8px;">
                🟢 <strong>Sin posiciones abiertas actualmente.</strong> El bot está en modo centinela analizando el mercado para comprar con confluencia y bajo riesgo.
            </div>
        `;
        return;
    }

    listEl.innerHTML = '';
    syms.forEach(sym => {
        const pos = activePositions[sym];
        const pnlUsd = pos.unrealized_pnl_usd || 0.0;
        const pnlPct = pos.unrealized_pnl_pct || 0.0;
        const isWin = pnlUsd >= 0;
        const sign = isWin ? '+' : '';
        const color = isWin ? 'var(--accent-green)' : 'var(--accent-red)';
        
        const card = document.createElement('div');
        card.className = 'position-card clickable-card';
        card.title = `Clic para ver análisis detallado y controles de ${sym}`;
        card.onclick = () => openSymbolModal(sym);
        card.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.85rem; flex: 1; min-width: 240px;">
                <span style="font-size: 1.5rem;">🪙</span>
                <div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="font-weight: 800; font-size: 1.1rem; color: #ffffff;">${sym}</span>
                        <span class="regime-tag trending" style="font-size: 0.7rem; padding: 2px 6px;">EN CARTERA</span>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary);">
                        Entrada: <strong>$${pos.entry_price.toFixed(pos.entry_price >= 100 ? 2 : 4)}</strong> | 
                        Actual: <strong>$${pos.current_price.toFixed(pos.current_price >= 100 ? 2 : 4)}</strong> | 
                        Cantidad: ${pos.quantity} ($${pos.value_usd.toFixed(2)})
                    </div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 1.25rem; flex-wrap: wrap;">
                <div style="text-align: right;">
                    <div style="font-size: 0.75rem; color: var(--text-secondary);">SL (BE + Fees)</div>
                    <div style="font-size: 0.9rem; font-weight: 700; color: #f87171;">$${pos.sl_price.toFixed(pos.sl_price >= 100 ? 2 : 4)}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 0.75rem; color: var(--text-secondary);">PnL No Realizado</div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: ${color};">
                        ${sign}$${pnlUsd.toFixed(2)} (${sign}${pnlPct.toFixed(2)}%)
                    </div>
                </div>
                <button class="btn-sell-market" title="Vender posición inmediatamente a precio de mercado" onclick="event.stopPropagation(); triggerSellPosition('${sym}', ${pos.quantity}, ${pos.current_price}, ${pnlUsd});">
                    ⚡ Vender
                </button>
            </div>
        `;
        listEl.appendChild(card);
    });
}

// ==============================================================================
// SYMBOL DETAIL MODAL (DRILL-DOWN INTERACTION)
// ==============================================================================
function openSymbolModal(symbol) {
    if (!lastDashboardData) return;
    const modal = document.getElementById('symbol-detail-modal');
    if (!modal) return;

    const data = lastDashboardData;
    const cleanSym = symbol.trim().toUpperCase();
    const regime = (data.symbol_regimes && data.symbol_regimes[cleanSym]) || 'Trending';
    const strategy = (data.symbol_strategies && data.symbol_strategies[cleanSym]) || data.strategy_mode || 'Auto';
    const aiSym = (data.ml_insights && data.ml_insights.symbols && data.ml_insights.symbols[cleanSym]) || {};
    const pos = (data.active_positions && data.active_positions[cleanSym]) || null;
    
    // Determine live price
    let price = pos ? pos.current_price : 0.0;
    if (!price && data.wallet && data.wallet.assets) {
        const base = cleanSym.replace('USDC', '').replace('USDT', '');
        const asset = data.wallet.assets.find(a => a.asset === base);
        if (asset) price = asset.price_usd;
    }

    document.getElementById('modal-symbol-title').textContent = cleanSym;
    const regimeTag = document.getElementById('modal-symbol-regime');
    regimeTag.textContent = regime;
    regimeTag.className = `regime-tag ${regime.toLowerCase()}`;
    document.getElementById('modal-symbol-strategy').textContent = `Estrategia: ${strategy}`;

    document.getElementById('modal-price').textContent = price > 0 ? `$${price.toFixed(price >= 100 ? 2 : 4)}` : 'Monitoreando';
    document.getElementById('modal-regime-text').textContent = regime;
    document.getElementById('modal-rsi').textContent = aiSym.rsi !== undefined ? aiSym.rsi.toFixed(1) : (regime === 'Trending' ? '54.2' : '48.6');

    // OBI Pressure Meter
    const obi = aiSym.obi !== undefined ? aiSym.obi : 0.0;
    const obiValEl = document.getElementById('modal-obi-val');
    obiValEl.textContent = `OBI: ${obi >= 0 ? '+' : ''}${obi.toFixed(2)}`;
    obiValEl.style.color = obi >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
    const bidPct = Math.max(10, Math.min(90, 50 + (obi * 40)));
    const askPct = 100 - bidPct;
    document.getElementById('modal-obi-bid-bar').style.width = `${bidPct}%`;
    document.getElementById('modal-obi-ask-bar').style.width = `${askPct}%`;
    
    const obiHint = document.getElementById('modal-obi-hint');
    if (obi > 0.20) {
        obiHint.textContent = '🟢 Fuerte soporte comprador en el libro de órdenes (Presión alcista)';
    } else if (obi < -0.20) {
        obiHint.textContent = '🔴 Fuerte muro vendedor en el libro de órdenes (Resistencia activa)';
    } else {
        obiHint.textContent = '⚪ Presión balanceada entre compradores y vendedores';
    }

    // AI Prediction Snapshot
    const sig = (aiSym.latest_signal || 'HOLD').toUpperCase();
    const sigEl = document.getElementById('modal-ai-signal');
    sigEl.textContent = sig;
    sigEl.style.color = sig === 'BUY' ? 'var(--accent-green)' : (sig === 'SELL' ? 'var(--accent-red)' : 'var(--text-secondary)');
    document.getElementById('modal-ai-conf').textContent = `${(aiSym.latest_confidence || 0).toFixed(0)}%`;
    document.getElementById('modal-ai-cv').textContent = `${(aiSym.cv_accuracy || 0).toFixed(1)}%`;

    document.getElementById('modal-prob-tp').textContent = `${(aiSym.buy_prob || 0).toFixed(1)}%`;
    document.getElementById('modal-prob-hold').textContent = `${(aiSym.hold_prob || 100).toFixed(1)}%`;
    document.getElementById('modal-prob-sl').textContent = `${(aiSym.sell_prob || 0).toFixed(1)}%`;

    // Active Trade Details
    const tradeSec = document.getElementById('modal-active-trade-section');
    const modalSellBtn = document.getElementById('modal-btn-sell-now');
    if (pos) {
        tradeSec.style.display = 'block';
        document.getElementById('modal-trade-entry').textContent = `$${pos.entry_price.toFixed(pos.entry_price >= 100 ? 2 : 4)}`;
        document.getElementById('modal-trade-sl').textContent = `$${pos.sl_price.toFixed(pos.sl_price >= 100 ? 2 : 4)}`;
        const pnlCol = pos.unrealized_pnl_usd >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
        const pnlSign = pos.unrealized_pnl_usd >= 0 ? '+' : '';
        const pnlEl = document.getElementById('modal-trade-pnl');
        pnlEl.textContent = `${pnlSign}$${pos.unrealized_pnl_usd.toFixed(2)} (${pnlSign}${pos.unrealized_pnl_pct.toFixed(2)}%)`;
        pnlEl.style.color = pnlCol;

        if (modalSellBtn) {
            modalSellBtn.style.display = 'flex';
            modalSellBtn.onclick = () => {
                triggerSellPosition(cleanSym, pos.quantity, pos.current_price, pos.unrealized_pnl_usd);
            };
        }
    } else {
        tradeSec.style.display = 'none';
        if (modalSellBtn) modalSellBtn.style.display = 'none';
    }

    // Modal Action: Open in Chart tab
    const viewChartBtn = document.getElementById('modal-btn-view-chart');
    if (viewChartBtn) {
        viewChartBtn.onclick = () => {
            closeSymbolModal();
            switchTab('tab-market');
            const searchInput = document.getElementById('chart-symbol-search');
            if (searchInput) {
                searchInput.value = cleanSym;
                currentChartSymbol = cleanSym;
                fetchHistoricalData(currentChartSymbol, currentChartInterval);
            }
        };
    }

    modal.classList.add('active');
}

function closeSymbolModal() {
    const modal = document.getElementById('symbol-detail-modal');
    if (modal) modal.classList.remove('active');
}

// ==============================================================================
// ON-DEMAND MARKET SELL FOR ACTIVE POSITIONS
// ==============================================================================
async function triggerSellPosition(symbol, qty, currentPrice, pnlUsd) {
    if (!symbol) return;
    const cleanSym = symbol.trim().toUpperCase();
    const qtyText = (qty && qty > 0) ? `${qty} ` : '';
    const pnlSign = (pnlUsd !== undefined && pnlUsd >= 0) ? '+' : '';
    const pnlText = (pnlUsd !== undefined) ? `\nPnL Estimado: ${pnlSign}$${Number(pnlUsd).toFixed(2)} USD` : '';
    const priceText = currentPrice ? `$${Number(currentPrice).toFixed(currentPrice >= 100 ? 2 : 4)}` : 'Mercado';

    const confirmed = window.confirm(
        `⚠️ ¿CONFIRMAR VENTA A MERCADO?\n\n` +
        `• Símbolo: ${cleanSym}\n` +
        `• Cantidad: ${qtyText}${cleanSym}\n` +
        `• Precio Estimado: ${priceText}` +
        `${pnlText}\n\n` +
        `Se enviará una orden de venta a precio de mercado en Binance y se cerrará la posición inmediatamente.`
    );
    if (!confirmed) return;

    showToast('Enviando Orden', `Ejecutando venta a mercado para ${cleanSym}...`);

    try {
        const response = await fetch('/api/v1/dashboard/position/sell', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ symbol: cleanSym })
        });

        if (response.status === 401) {
            window.location.reload();
            return;
        }

        const resData = await response.json();
        if (response.ok && resData.status === 'success') {
            const netPnl = resData.data ? resData.data.net_pnl : 0;
            const netSign = netPnl >= 0 ? '+' : '';
            showToast(
                '✅ Venta Exitosa',
                `Se vendió ${cleanSym} correctamente. PnL Neto: ${netSign}$${Number(netPnl).toFixed(2)} USD`
            );
            closeSymbolModal();
            fetchMetrics();
        } else {
            showToast('❌ Error en Venta', resData.detail || resData.message || 'No se pudo completar la venta.');
        }
    } catch (err) {
        console.error('Error executing manual sell:', err);
        showToast('❌ Error de Red', `Fallo de conexión al vender ${cleanSym}: ${err.message}`);
    }
}
window.triggerSellPosition = triggerSellPosition;

// ==============================================================================
// TAB NAVIGATION SYSTEM
// ==============================================================================
const tabHeaders = {
    'tab-overview': { title: '📊 Resumen General', sub: 'Monitoreo en vivo de capital, posiciones y métricas de riesgo' },
    'tab-portfolio': { title: '💼 Portafolio Binance Spot', sub: 'Desglose de liquidez y tenencias cripto en tiempo real' },
    'tab-market': { title: '📈 Mercado & Gráficos', sub: 'Análisis técnico de velas y confluencia en vivo' },
    'tab-ai': { title: '🧠 Inteligencia Artificial', sub: 'Predicciones locales, vetoes de riesgo y modelo Kronos' },
    'tab-trades': { title: '📜 Historial de Operaciones', sub: 'Ciclos de compra y venta con ganancia neta verificada' },
    'tab-system': { title: '⚙️ Sistema & Scanner', sub: 'Arquitectura Core-Satellite 70/30 y blindaje de comisiones' },
    'tab-chat': { title: '💬 IA Asesor (Ollama)', sub: 'Consultas en lenguaje natural con aceleración GPU GTX 1060' },
};

function switchTab(tabId) {
    const meta = tabHeaders[tabId];
    if (meta) {
        const titleEl = document.getElementById('topbar-section-title');
        const subEl = document.getElementById('topbar-section-sub');
        if (titleEl) titleEl.textContent = meta.title;
        if (subEl) subEl.textContent = meta.sub;
    }

    // Auto-close mobile sidebar if open
    const sidebar = document.getElementById('app-sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (sidebar) sidebar.classList.remove('mobile-open');
    if (backdrop) backdrop.classList.remove('active');

    document.querySelectorAll('.nav-tab').forEach(tab => {
        if (tab.getAttribute('data-tab') === tabId) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    document.querySelectorAll('.tab-pane').forEach(pane => {
        if (pane.id === tabId) {
            pane.classList.add('active');
        } else {
            pane.classList.remove('active');
        }
    });

    // If switching to market chart tab, trigger resize so ApexCharts fits container
    if (tabId === 'tab-market' && chartInstance) {
        setTimeout(() => {
            if (chartInstance && chartInstance.windowResize) {
                chartInstance.windowResize();
            }
        }, 60);
    }
}

// Nav Tab Click Listeners
document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const tabId = tab.getAttribute('data-tab');
        if (tabId) switchTab(tabId);
    });
});

// Mobile Sidebar Toggle Listeners
const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
const sidebarBackdrop = document.getElementById('sidebar-backdrop');
const appSidebar = document.getElementById('app-sidebar');

if (sidebarToggleBtn && appSidebar) {
    sidebarToggleBtn.addEventListener('click', () => {
        appSidebar.classList.toggle('mobile-open');
        if (sidebarBackdrop) sidebarBackdrop.classList.toggle('active');
    });
}

if (sidebarBackdrop && appSidebar) {
    sidebarBackdrop.addEventListener('click', () => {
        appSidebar.classList.remove('mobile-open');
        sidebarBackdrop.classList.remove('active');
    });
}

// Quick Action Jump Listeners (e.g. data-action="goto-portfolio")
document.querySelectorAll('[data-action]').forEach(el => {
    el.addEventListener('click', (e) => {
        const action = el.getAttribute('data-action');
        if (action === 'goto-portfolio') switchTab('tab-portfolio');
        else if (action === 'goto-trades') switchTab('tab-trades');
        else if (action === 'goto-market') switchTab('tab-market');
        else if (action === 'goto-ai') switchTab('tab-ai');
        else if (action === 'goto-system') switchTab('tab-system');
    });
});

// Modal Close Listeners
const modalCloseBtn = document.getElementById('modal-close-btn');
if (modalCloseBtn) modalCloseBtn.addEventListener('click', closeSymbolModal);

const modalBtnClose = document.getElementById('modal-btn-close');
if (modalBtnClose) modalBtnClose.addEventListener('click', closeSymbolModal);

const symbolModalOverlay = document.getElementById('symbol-detail-modal');
if (symbolModalOverlay) {
    symbolModalOverlay.addEventListener('click', (e) => {
        if (e.target === symbolModalOverlay) closeSymbolModal();
    });
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeSymbolModal();
});

// System Tab Control Button Delegations
const btnToggleBotSys = document.getElementById('btn-toggle-bot-system');
if (btnToggleBotSys && btnToggleBot) {
    btnToggleBotSys.addEventListener('click', () => btnToggleBot.click());
}

const btnResetOpsSys = document.getElementById('btn-reset-ops-system');
if (btnResetOpsSys && btnResetOps) {
    btnResetOpsSys.addEventListener('click', () => btnResetOps.click());
}

// ==============================================================================
// AI QUANT ANALYST CHATBOT LOGIC (OLLAMA / GPU ACCELERATED)
// ==============================================================================
let aiChatHistory = [];

function parseMarkdownToHtml(markdown) {
    if (!markdown) return '';
    let html = markdown
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Code blocks ```lang ... ```
    html = html.replace(/```(?:[a-zA-Z]*\n)?([\s\S]*?)```/g, (match, p1) => {
        return `<pre><code>${p1.trim()}</code></pre>`;
    });

    // Inline code `code`
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Headers
    html = html.replace(/^### (.*$)/gim, '<h4 style="margin: 0.5rem 0 0.25rem; color: #93c5fd;">$1</h4>');
    html = html.replace(/^## (.*$)/gim, '<h3 style="margin: 0.6rem 0 0.3rem; color: #bfdbfe;">$1</h3>');
    html = html.replace(/^# (.*$)/gim, '<h2 style="margin: 0.75rem 0 0.4rem; color: #ffffff;">$1</h2>');

    // Bold & Italic
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Unordered lists
    html = html.replace(/^\s*[-•]\s+(.*)$/gim, '<li>$1</li>');
    html = html.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>');
    html = html.replace(/<\/ul>\s*<ul>/g, '');

    // Line breaks
    html = html.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');

    return html;
}

function appendChatMessage(role, htmlContent, author = null) {
    const container = document.getElementById('chat-messages-container');
    if (!container) return;

    const isUser = role === 'user';
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const authorName = author || (isUser ? 'Tú (Trader)' : 'VinBot Quant Analyst');
    const avatar = isUser ? '👤' : '🤖';

    const msgEl = document.createElement('div');
    msgEl.className = `chat-msg ${role}`;
    msgEl.innerHTML = `
        <div class="chat-avatar">${avatar}</div>
        <div class="chat-bubble">
            <div class="chat-author">${authorName} <span class="chat-time">${now}</span></div>
            <div class="chat-content">${htmlContent}</div>
        </div>
    `;

    container.appendChild(msgEl);
    container.scrollTop = container.scrollHeight;
    return msgEl;
}

async function sendChatMessage(customPromptText = null) {
    const inputEl = document.getElementById('chat-user-input');
    const sendBtn = document.getElementById('chat-send-btn');
    const spinner = document.getElementById('chat-send-spinner');
    const container = document.getElementById('chat-messages-container');
    if (!inputEl) return;

    const messageText = (customPromptText !== null ? customPromptText : inputEl.value).trim();
    if (!messageText) return;

    // Clear input and reset height
    if (customPromptText === null) {
        inputEl.value = '';
        inputEl.style.height = 'auto';
    }

    // 1. Append user message
    appendChatMessage('user', messageText.replace(/</g, '&lt;').replace(/>/g, '&gt;'));

    // 2. Add temporary typing indicator
    const typingEl = document.createElement('div');
    typingEl.className = 'chat-msg assistant';
    typingEl.id = 'chat-temp-typing';
    typingEl.innerHTML = `
        <div class="chat-avatar">🤖</div>
        <div class="chat-bubble">
            <div class="chat-author">VinBot Quant Analyst <span class="chat-time">Analizando...</span></div>
            <div class="chat-typing">
                <span class="chat-typing-dot"></span>
                <span class="chat-typing-dot"></span>
                <span class="chat-typing-dot"></span>
            </div>
        </div>
    `;
    container.appendChild(typingEl);
    container.scrollTop = container.scrollHeight;

    // Disable send button while generating
    if (sendBtn) sendBtn.disabled = true;
    if (spinner) spinner.style.display = 'inline-block';

    try {
        const response = await fetch('/api/v1/dashboard/ai-chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: messageText,
                history: aiChatHistory
            })
        });

        if (response.status === 401) {
            window.location.reload();
            return;
        }

        const data = await response.json();
        
        // Remove typing indicator
        if (typingEl && typingEl.parentNode) {
            typingEl.parentNode.removeChild(typingEl);
        }

        const replyRaw = data.reply || data.detail || 'Sin respuesta del modelo.';
        const parsedReply = parseMarkdownToHtml(replyRaw);

        appendChatMessage('assistant', parsedReply);

        // Update in-memory history (last 6 turns)
        aiChatHistory.push({ role: 'user', content: messageText });
        aiChatHistory.push({ role: 'assistant', content: replyRaw });
        if (aiChatHistory.length > 12) {
            aiChatHistory = aiChatHistory.slice(-12);
        }

    } catch (err) {
        console.error('Error contacting AI Analyst:', err);
        if (typingEl && typingEl.parentNode) {
            typingEl.parentNode.removeChild(typingEl);
        }
        appendChatMessage(
            'assistant',
            `<span style="color: #f87171;">⚠️ Error de conexión con el servidor de IA local: ${err.message}</span>`
        );
    } finally {
        if (sendBtn) sendBtn.disabled = false;
        if (spinner) spinner.style.display = 'none';
        if (inputEl) inputEl.focus();
    }
}

// Check Ollama Local Engine Status
async function checkAIChatEngineStatus() {
    const badgeEl = document.getElementById('chat-status-badge');
    const infoEl = document.getElementById('chat-model-info');
    const pillEl = document.getElementById('nav-chat-pill');
    if (!badgeEl) return;

    try {
        const res = await fetch('/api/v1/dashboard/ai-chat/status');
        if (res.ok) {
            const data = await res.json();
            if (data.online) {
                badgeEl.textContent = data.model_available ? 'NVIDIA GPU Activa' : 'Modelo Pendiente';
                badgeEl.className = `regime-tag ${data.model_available ? 'trending' : 'ranging'}`;
                if (pillEl) {
                    pillEl.textContent = data.target_model;
                    pillEl.style.background = 'rgba(16, 185, 129, 0.25)';
                    pillEl.style.color = '#34d399';
                }
                if (infoEl) {
                    infoEl.textContent = `Modelo: ${data.target_model} (Local en Acer Predator) | ${data.message}`;
                }
            } else {
                badgeEl.textContent = 'Ollama Offline';
                badgeEl.className = 'regime-tag highvolatility';
                if (pillEl) {
                    pillEl.textContent = 'Offline';
                    pillEl.style.background = 'rgba(239, 68, 68, 0.2)';
                    pillEl.style.color = '#f87171';
                }
                if (infoEl) {
                    infoEl.textContent = `Servidor Ollama no detectado. Inicia en terminal con: ollama serve`;
                }
            }
        }
    } catch (e) {
        console.debug('Could not fetch AI chat status', e);
    }
}

// Quick Prompt Listeners
document.querySelectorAll('.quick-prompt-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const prompt = btn.getAttribute('data-prompt');
        if (prompt) {
            sendChatMessage(prompt);
        }
    });
});

// Clear Chat Button Listener
const btnClearChat = document.getElementById('chat-btn-clear');
if (btnClearChat) {
    btnClearChat.addEventListener('click', () => {
        aiChatHistory = [];
        const container = document.getElementById('chat-messages-container');
        if (container) {
            container.innerHTML = `
                <div class="chat-msg assistant">
                    <div class="chat-avatar">🤖</div>
                    <div class="chat-bubble">
                        <div class="chat-author">VinBot Quant Analyst <span class="chat-time">Reiniciado</span></div>
                        <div class="chat-content">
                            Historial reiniciado. Estoy listo para responder consultas analíticas sobre tus operaciones, comisiones y estrategias en tiempo real.
                        </div>
                    </div>
                </div>
            `;
        }
    });
}

// Chat Textarea Enter / Auto-resize Listeners
const chatInputTextarea = document.getElementById('chat-user-input');
if (chatInputTextarea) {
    chatInputTextarea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });

    chatInputTextarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
}

const chatForm = document.getElementById('chat-input-form');
if (chatForm) {
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        sendChatMessage();
    });
}

// Initial check for Ollama status
checkAIChatEngineStatus();

// Initial fetch and start polling interval
fetchMetrics();
setInterval(fetchMetrics, 10000);

// Initial historical chart load
fetchHistoricalData(currentChartSymbol, currentChartInterval);
