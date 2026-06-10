"""
Tests for backtesting engine.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Mock settings before importing
@pytest.fixture(autouse=True)
def mock_settings():
    with patch('app.services.backtest.engine.get_settings') as mock:
        mock.return_value = MagicMock(
            BACKTEST_INITIAL_CAPITAL=1000.0,
            BACKTEST_SLIPPAGE_MAJORS=0.001,
            BACKTEST_SLIPPAGE_ALTS=0.002,
            BACKTEST_COMMISSION=0.001
        )
        yield mock


class TestBacktestEngine:
    """Tests for BacktestEngine."""

    @pytest.fixture
    def engine(self):
        from app.services.backtest.engine import BacktestEngine
        return BacktestEngine(initial_capital=1000.0)

    @pytest.fixture
    def sample_klines(self):
        """Create sample klines for testing."""
        from app.services.backtest.data_fetcher import Kline

        klines = []
        base_price = 50000.0
        for i in range(100):
            klines.append(Kline(
                timestamp=1700000000000 + i * 3600000,  # 1 hour intervals
                open=base_price + i * 10,
                high=base_price + i * 10 + 100,
                low=base_price + i * 10 - 100,
                close=base_price + i * 10 + 50,
                volume=1000.0,
                close_time=1700000000000 + (i + 1) * 3600000
            ))
        return klines

    def test_engine_initialization(self, engine):
        """Test engine initializes correctly."""
        assert engine.initial_capital == 1000.0
        assert engine.slippage_majors == 0.001
        assert engine.commission == 0.001

    def test_is_major_symbol(self, engine):
        """Test major symbol detection."""
        assert engine._is_major_symbol("BTCUSDT") == True
        assert engine._is_major_symbol("ETHUSDT") == True
        assert engine._is_major_symbol("SOLUSDT") == False

    def test_apply_slippage_buy(self, engine):
        """Test slippage applied to buy orders."""
        price = 50000.0
        result = engine._apply_slippage(price, "BUY", True)
        assert abs(result - 50050.0) < 0.01  # +0.1%

    def test_apply_slippage_sell(self, engine):
        """Test slippage applied to sell orders."""
        price = 50000.0
        result = engine._apply_slippage(price, "SELL", True)
        assert result == 49950.0  # -0.1%

    def test_calculate_commission(self, engine):
        """Test commission calculation."""
        comm = engine._calculate_commission(50000.0, 0.1)
        assert comm == 5.0  # 50000 * 0.1 * 0.001

    def test_calculate_position_size(self, engine):
        """Test position size calculation."""
        size = engine._calculate_position_size(
            capital=1000.0,
            price=50000.0,
            stop_loss_pct=2.0,
            risk_pct=1.0
        )
        # Risk = 10, stop = 1000 (2% of 50000), size = 10/1000 = 0.01
        assert size > 0

    def test_calculate_rsi(self, engine):
        """Test RSI calculation."""
        from app.services.backtest.data_fetcher import Kline

        # Create oscillating prices
        klines = []
        for i in range(20):
            price = 50000 + (100 if i % 2 == 0 else -100)
            klines.append(Kline(
                timestamp=i * 3600000,
                open=price, high=price, low=price, close=price,
                volume=1000, close_time=(i+1) * 3600000
            ))

        rsi = engine._calculate_rsi(klines)
        assert rsi is not None
        assert 0 <= rsi <= 100


class TestBacktestMetrics:
    """Tests for metrics calculation."""

    @pytest.fixture
    def sample_result(self):
        """Create sample backtest result."""
        from app.services.backtest.engine import BacktestResult, Trade

        result = BacktestResult(
            strategy_name="RSI",
            symbol="BTCUSDT",
            timeframe="1h",
            start_date="2024-01-01",
            end_date="2024-12-31",
            initial_capital=1000.0,
            final_capital=1200.0,
            total_pnl=200.0,
            total_pnl_pct=20.0
        )

        # Add sample trades
        result.trades = [
            Trade(
                entry_time=datetime(2024, 1, 1),
                exit_time=datetime(2024, 1, 2),
                entry_price=50000.0,
                exit_price=51000.0,
                side=MagicMock(value="BUY"),
                pnl=100.0,
                pnl_pct=2.0,
                quantity=0.1,
                commission=5.0,
                duration_hours=24.0
            ),
            Trade(
                entry_time=datetime(2024, 1, 3),
                exit_time=datetime(2024, 1, 4),
                entry_price=51000.0,
                exit_price=50000.0,
                side=MagicMock(value="SELL"),
                pnl=-50.0,
                pnl_pct=-1.0,
                quantity=0.05,
                commission=2.5,
                duration_hours=24.0
            )
        ]

        result.equity_curve = [
            {"timestamp": 1700000000000, "equity": 1000.0},
            {"timestamp": 1700100000000, "equity": 1100.0},
            {"timestamp": 1700200000000, "equity": 1050.0},
            {"timestamp": 1700300000000, "equity": 1200.0}
        ]

        return result

    def test_calculate_total_pnl(self, sample_result):
        """Test total PnL calculation."""
        from app.services.backtest.metrics import calculate_metrics

        metrics = calculate_metrics(sample_result)

        assert metrics['total_pnl'] == 200.0
        assert metrics['total_pnl_pct'] == 20.0

    def test_calculate_win_rate(self, sample_result):
        """Test win rate calculation."""
        from app.services.backtest.metrics import calculate_metrics

        metrics = calculate_metrics(sample_result)

        # 1 win out of 2 trades = 50%
        assert metrics['win_rate'] == 50.0

    def test_calculate_profit_factor(self, sample_result):
        """Test profit factor calculation."""
        from app.services.backtest.metrics import calculate_metrics

        metrics = calculate_metrics(sample_result)

        # profit factor = 100 / 50 = 2
        assert metrics['profit_factor'] == 2.0

    def test_calculate_max_drawdown(self, sample_result):
        """Test max drawdown calculation."""
        from app.services.backtest.metrics import calculate_metrics

        metrics = calculate_metrics(sample_result)

        # From 1100 to 1050 = ~4.5%
        assert metrics['max_drawdown'] > 0


class TestDataFetcher:
    """Tests for historical data fetcher."""

    def test_kline_interval_validation(self):
        """Test invalid interval raises error."""
        from app.services.backtest.data_fetcher import HistoricalDataFetcher

        fetcher = HistoricalDataFetcher()

        with pytest.raises(ValueError):
            fetcher.fetch_klines("BTCUSDT", "invalid_interval")

    def test_valid_intervals(self):
        """Test valid intervals accepted."""
        from app.services.backtest.data_fetcher import HistoricalDataFetcher, KLINE_INTERVALS

        fetcher = HistoricalDataFetcher()

        for interval in KLINE_INTERVALS:
            assert interval in ["1m", "5m", "15m", "1h", "4h", "1d"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])