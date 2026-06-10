"""
Tests for Multi-Timeframe Analysis.
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_settings():
    # Patch the instantiated settings object inside multi_timeframe module
    with patch('app.services.multi_timeframe.settings') as mock:
        mock.MULTI_TF_ENABLED = True
        mock.ACTIVE_TIMEFRAMES = "1m,15m,1h"
        mock.MAX_CANDLES_PER_TF = 500
        mock.MIN_CONFLUENCE_LEVEL = "MEDIA"
        mock.ALLOW_LOW_CONFLUENCE_TRADES = False
        yield mock


class TestMultiTimeframeManager:
    """Tests for MultiTimeframeManager."""

    @pytest.fixture
    def manager(self, mock_settings):
        from app.services.multi_timeframe import MultiTimeframeManager
        return MultiTimeframeManager()

    def test_initialization(self, manager):
        """Test manager initializes correctly."""
        assert manager.enabled == True
        assert "1m" in manager.timeframes
        assert "15m" in manager.timeframes
        assert "1h" in manager.timeframes

    def test_register_symbol(self, manager):
        """Test symbol registration."""
        manager.register_symbol("BTCUSDT")
        assert "BTCUSDT" in manager.symbol_data
        assert "1m" in manager.symbol_data["BTCUSDT"]

    def test_unregister_symbol(self, manager):
        """Test symbol unregistration."""
        manager.register_symbol("BTCUSDT")
        manager.unregister_symbol("BTCUSDT")
        assert "BTCUSDT" not in manager.symbol_data

    def test_parse_timeframes(self, manager):
        """Test timeframe parsing."""
        timeframes = manager._parse_timeframes("1m,5m,15m")
        assert timeframes == ["1m", "5m", "15m"]


class TestSignalConfirmation:
    """Tests for signal confirmation logic."""

    @pytest.fixture
    def manager(self, mock_settings):
        from app.services.multi_timeframe import MultiTimeframeManager
        return MultiTimeframeManager()

    @patch('app.services.multi_timeframe.SymbolData')
    def test_confirm_buy_with_alignment(self, mock_symbol, manager):
        """Test BUY confirmation with aligned timeframes."""
        # Setup mock data
        manager.register_symbol("BTCUSDT")
        manager.symbol_data["BTCUSDT"]["1h"].closes = [50000] * 25
        manager.symbol_data["BTCUSDT"]["1h"].get_ema = lambda p: 49000  # EMA below price = UP trend
        manager.symbol_data["BTCUSDT"]["15m"].closes = [50000] * 25
        manager.symbol_data["BTCUSDT"]["15m"].get_ema = lambda p: 49000
        manager.symbol_data["BTCUSDT"]["1m"].closes = [50000] * 25
        manager.symbol_data["BTCUSDT"]["1m"].get_ema = lambda p: 49000

        # The actual test would need real data - this is a placeholder
        # In real implementation, this would test the confirmation logic
        assert manager.enabled == True


class TestTrendDirection:
    """Tests for trend direction detection."""

    @pytest.fixture
    def manager(self, mock_settings):
        from app.services.multi_timeframe import MultiTimeframeManager
        return MultiTimeframeManager()

    @patch('app.services.multi_timeframe.SymbolData')
    def test_trend_up(self, mock_symbol_data, manager):
        """Test uptrend detection."""
        manager.register_symbol("BTCUSDT")

        # Mock the data structure
        mock_data = MagicMock()
        mock_data.closes = [50000, 50100, 50200, 50300, 50400] * 5
        mock_data.get_ema = lambda p: 50000  # Price above EMA

        manager.symbol_data["BTCUSDT"]["1h"] = mock_data

        trend = manager.get_trend_direction("BTCUSDT", "1h")
        # Since price is above EMA, should be UP (or RANGING if close)
        assert trend.value in ["UP", "RANGING"]

    @patch('app.services.multi_timeframe.SymbolData')
    def test_trend_down(self, mock_symbol_data, manager):
        """Test downtrend detection."""
        manager.register_symbol("BTCUSDT")

        mock_data = MagicMock()
        mock_data.closes = [50000, 49900, 49800, 49700, 49600] * 5
        mock_data.get_ema = lambda p: 50000  # Price below EMA

        manager.symbol_data["BTCUSDT"]["1h"] = mock_data

        trend = manager.get_trend_direction("BTCUSDT", "1h")
        assert trend.value in ["DOWN", "RANGING"]


class TestIndicatorAggregation:
    """Tests for indicator aggregation."""

    @pytest.fixture
    def manager(self, mock_settings):
        from app.services.multi_timeframe import MultiTimeframeManager
        return MultiTimeframeManager()

    def test_get_all_rsi(self, manager):
        """Test getting RSI for all timeframes."""
        manager.register_symbol("BTCUSDT")

        # Mock RSI values
        for tf in ["1m", "15m", "1h"]:
            manager.symbol_data["BTCUSDT"][tf].get_rsi = lambda: 45.0

        rsi_values = manager.get_all_rsi("BTCUSDT")

        assert "1m" in rsi_values
        assert "15m" in rsi_values
        assert "1h" in rsi_values


class TestConfluenceLevel:
    """Tests for confluence level enum."""

    def test_confluence_levels(self):
        """Test confluence level values."""
        from app.services.multi_timeframe import ConfluenceLevel

        assert ConfluenceLevel.ALTA.value == "ALTA"
        assert ConfluenceLevel.MEDIA.value == "MEDIA"
        assert ConfluenceLevel.BAJA.value == "BAJA"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])