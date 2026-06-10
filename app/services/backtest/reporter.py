"""
HTML report generation for backtest results.
"""
import logging
from typing import Dict, Any, List

from app.services.backtest.engine import BacktestResult, Trade
from app.services.backtest.metrics import calculate_metrics, format_metrics

logger = logging.getLogger(__name__)


def generate_report(result: BacktestResult) -> str:
    """
    Generate HTML report from backtest result.

    Returns:
        HTML string with embedded CSS and charts
    """
    metrics = calculate_metrics(result)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backtest Report - {result.strategy_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1, h2, h3 {{ color: #fff; margin-bottom: 15px; }}
        h1 {{ border-bottom: 2px solid #00d4aa; padding-bottom: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .metric {{ background: #16213e; padding: 15px; border-radius: 8px; text-align: center; }}
        .metric .label {{ color: #888; font-size: 12px; text-transform: uppercase; }}
        .metric .value {{ font-size: 24px; font-weight: bold; color: #00d4aa; }}
        .metric .value.negative {{ color: #ff4757; }}
        .positive {{ color: #2ed573; }}
        .negative {{ color: #ff4757; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #333; }}
        th {{ background: #16213e; color: #00d4aa; }}
        tr:hover {{ background: #16213e; }}
        .chart-container {{ background: #16213e; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .chart {{ width: 100%; height: 300px; }}
        .trades-list {{ max-height: 400px; overflow-y: auto; }}
        .trade {{ padding: 10px; margin: 5px 0; background: #16213e; border-radius: 4px; display: flex; justify-content: space-between; }}
        .trade.win {{ border-left: 3px solid #2ed573; }}
        .trade.loss {{ border-left: 3px solid #ff4757; }}
        .section {{ margin: 30px 0; }}
        .btn {{ display: inline-block; padding: 10px 20px; background: #00d4aa; color: #1a1a2e; text-decoration: none; border-radius: 4px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Backtest Report</h1>
        <p><strong>Strategy:</strong> {result.strategy_name}</p>
        <p><strong>Symbol:</strong> {result.symbol} | <strong>Timeframe:</strong> {result.timeframe}</p>
        <p><strong>Period:</strong> {result.start_date} to {result.end_date}</p>
        <p><strong>Runtime:</strong> {result.run_time_seconds:.2f}s | <strong>Candles:</strong> {result.total_candles}</p>

        <div class="section">
            <h2>📈 Summary</h2>
            <div class="summary">
                <div class="metric">
                    <div class="label">Total PnL</div>
                    <div class="value {'negative' if metrics['total_pnl'] < 0 else ''}">${metrics['total_pnl']:.2f}</div>
                    <div class="value {'negative' if metrics['total_pnl_pct'] < 0 else ''}">({metrics['total_pnl_pct']:.2f}%)</div>
                </div>
                <div class="metric">
                    <div class="label">Final Capital</div>
                    <div class="value">${metrics['final_capital']:.2f}</div>
                </div>
                <div class="metric">
                    <div class="label">Win Rate</div>
                    <div class="value">{metrics['win_rate']:.1f}%</div>
                </div>
                <div class="metric">
                    <div class="label">Profit Factor</div>
                    <div class="value">{metrics['profit_factor']:.2f}</div>
                </div>
                <div class="metric">
                    <div class="label">Sharpe Ratio</div>
                    <div class="value">{metrics['sharpe_ratio']:.2f}</div>
                </div>
                <div class="metric">
                    <div class="label">Max Drawdown</div>
                    <div class="value negative">{metrics['max_drawdown']:.2f}%</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>📋 Trade Statistics</h2>
            <table>
                <tr><td>Total Trades</td><td>{metrics['total_trades']}</td></tr>
                <tr><td>Winning Trades</td><td class="positive">{metrics['winning_trades']}</td></tr>
                <tr><td>Losing Trades</td><td class="negative">{metrics['losing_trades']}</td></tr>
                <tr><td>Avg Trade</td><td class="{'positive' if metrics['avg_trade'] > 0 else 'negative'}">${metrics['avg_trade']:.2f}</td></tr>
                <tr><td>Avg Win</td><td class="positive">${metrics['avg_win']:.2f}</td></tr>
                <tr><td>Avg Loss</td><td class="negative">${metrics['avg_loss']:.2f}</td></tr>
                <tr><td>Expectancy</td><td class="{'positive' if metrics['expectancy'] > 0 else 'negative'}">${metrics['expectancy']:.2f}</td></tr>
                <tr><td>Total Commission</td><td>${metrics['total_commission']:.2f}</td></tr>
                <tr><td>Max Consecutive Wins</td><td>{metrics['max_consecutive_wins']}</td></tr>
                <tr><td>Max Consecutive Losses</td><td>{metrics['max_consecutive_losses']}</td></tr>
            </table>
        </div>

        <div class="section">
            <h2>📉 Equity Curve</h2>
            <div class="chart-container">
                <canvas id="equityChart"></canvas>
            </div>
        </div>

        <div class="section">
            <h2>📝 Trade History</h2>
            <div class="trades-list">
"""

    # Add trade rows
    for trade in result.trades[-50:]:  # Last 50 trades
        trade_class = "win" if trade.pnl > 0 else "loss"
        html += f"""
                <div class="trade {trade_class}">
                    <span>{trade.entry_time.strftime('%Y-%m-%d %H:%M')} → {trade.exit_time.strftime('%Y-%m-%d %H:%M')}</span>
                    <span>{trade.side.value} @ ${trade.entry_price:.2f} → ${trade.exit_price:.2f}</span>
                    <span class="{'positive' if trade.pnl > 0 else 'negative'}">${trade.pnl:.2f} ({trade.pnl_pct:.2f}%)</span>
                </div>
"""

    html += f"""
            </div>
        </div>

        <div class="section">
            <h2>⚙️ Configuration</h2>
            <table>
                <tr><td>Initial Capital</td><td>${result.config.get('initial_capital', result.initial_capital):.2f}</td></tr>
                <tr><td>Stop Loss</td><td>{result.config.get('stop_loss_pct', 2.0)}%</td></tr>
                <tr><td>Take Profit</td><td>{result.config.get('take_profit_pct', 5.0)}%</td></tr>
                <tr><td>Risk per Trade</td><td>{result.config.get('risk_per_trade_pct', 1.0)}%</td></tr>
                <tr><td>Slippage</td><td>{(result.config.get('slippage', 0.001) * 100):.2f}%</td></tr>
                <tr><td>Commission</td><td>{(result.config.get('commission', 0.001) * 100):.2f}%</td></tr>
            </table>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Equity curve chart
        const equityData = {result.equity_curve};

        const labels = equityData.map(e => new Date(e.timestamp).toLocaleDateString());
        const data = equityData.map(e => e.equity);

        new Chart(document.getElementById('equityChart'), {{
            type: 'line',
            data: {{
                labels: labels,
                datasets: [{{
                    label: 'Equity',
                    data: data,
                    borderColor: '#00d4aa',
                    backgroundColor: 'rgba(0, 212, 170, 0.1)',
                    fill: true,
                    tension: 0.1
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    x: {{ grid: {{ color: '#333' }}, ticks: {{ color: '#888' }} }},
                    y: {{ grid: {{ color: '#333' }}, ticks: {{ color: '#888' }} }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

    return html


def save_report(result: BacktestResult, filepath: str) -> str:
    """
    Save HTML report to file.

    Args:
        result: BacktestResult
        filepath: Output file path

    Returns:
        Path to saved file
    """
    import os

    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

    html = generate_report(result)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(f"Report saved to: {filepath}")
    return filepath