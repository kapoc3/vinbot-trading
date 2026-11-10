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
        card.className = 'symbol-card';
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

function renderClosedCycles(cycles) {
    const grid = document.getElementById('closed-cycles-grid');
    if (!grid) return;
    grid.innerHTML = '';

    if (!cycles || cycles.length === 0) {
        grid.innerHTML = '<div class="loading-placeholder">Aún no hay ventas cerradas que emparejen compras previas.</div>';
        return;
    }

    cycles.forEach(c => {
        const pnlUsd = c.pnl_usd || 0.0;
        const pnlPct = c.pnl_pct || 0.0;
        const isWin = pnlUsd >= 0;
        const pnlColor = isWin ? 'var(--accent-green)' : 'var(--accent-red)';
        const borderAccent = isWin ? 'rgba(16, 185, 129, 0.35)' : 'rgba(239, 68, 68, 0.35)';

        let dateStr = c.timestamp || '';
        if (c.timestamp) {
            const isoStr = c.timestamp.includes(' ') ? c.timestamp.replace(' ', 'T') : c.timestamp;
            const d = new Date(isoStr + 'Z');
            if (!isNaN(d.getTime())) dateStr = d.toLocaleString();
        }

        const detailsList = (c.matched_details || []).map(m =>
            `<div style="display: flex; justify-content: space-between; font-size: 0.76rem; color: var(--text-secondary);">
                <span>↳ Compra <b>#${m.buy_order_id}</b> (${m.qty} a $${parseFloat(m.buy_price).toFixed(2)})</span>
                <span style="color: ${m.pnl_usd >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'}; font-weight: 600;">${m.pnl_usd >= 0 ? '+' : ''}$${parseFloat(m.pnl_usd).toFixed(4)}</span>
            </div>`
        ).join('');

        const card = document.createElement('div');
        card.className = 'symbol-card';
        card.style.border = `1px solid ${borderAccent}`;
        card.innerHTML = `
            <div class="symbol-header" style="margin-bottom: 0.5rem;">
                <div>
                    <span class="symbol-name" style="font-size: 1rem;">${c.symbol}</span>
                    <span style="font-size: 0.75rem; color: var(--text-secondary); margin-left: 0.4rem;">Venta #${c.sell_order_id}</span>
                </div>
                <span class="side-badge ${isWin ? 'buy' : 'sell'}" style="font-size: 0.8rem;">
                    ${isWin ? '+' : ''}$${pnlUsd.toFixed(4)} USDC (${isWin ? '+' : ''}${pnlPct.toFixed(2)}%)
                </span>
            </div>
            <div style="font-size: 0.82rem; display: flex; flex-direction: column; gap: 0.35rem;">
                <div style="display: flex; justify-content: space-between;">
                    <span class="strategy-label">Fecha Venta:</span>
                    <span style="color: #e5e7eb;">${dateStr}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span class="strategy-label">Precio Compra Prom. → Venta:</span>
                    <span style="font-weight: 700; color: #f3f4f6;">$${parseFloat(c.avg_buy_price).toFixed(2)} → $${parseFloat(c.sell_price).toFixed(2)}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span class="strategy-label">Capital Invertido → Recuperado:</span>
                    <span style="font-weight: 600; color: ${pnlColor};">$${parseFloat(c.buy_cost_usd).toFixed(2)} → $${parseFloat(c.sell_value_usd).toFixed(2)} USDC</span>
                </div>
                <div style="margin-top: 0.35rem; padding-top: 0.35rem; border-top: 1px solid rgba(255,255,255,0.06);">
                    <div style="font-size: 0.75rem; font-weight: 600; color: #9ca3af; margin-bottom: 0.2rem;">Compras Asociadas (${(c.matched_details || []).length}):</div>
                    ${detailsList}
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
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
