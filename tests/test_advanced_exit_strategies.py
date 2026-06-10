import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTrailingTakeProfit:
    """Tests for Trailing Take Profit functionality."""

    @pytest.fixture
    def risk_manager(self):
        with patch('app.services.risk_manager.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                ENABLE_TRAILING_TP=True,
                TRAILING_TP_ATR_MULTIPLIER=2.0,
                TRAILING_TP_ACTIVATION_PCT=1.5,
                ENABLE_TIME_EXIT=False,
                MAX_HOLD_HOURS=4,
                TIME_EXIT_COOLDOWN_MINUTES=15,
                ENABLE_SIGNAL_STRENGTH_EXIT=False,
                ENABLE_DYNAMIC_PARTIAL_TP=True,
                STOP_LOSS_PCT=2.0,
                ALLOCATED_CAPITAL=1000,
                RISK_PER_TRADE_PCT=1.0,
                PARTIAL_TP_LEVELS="1.0:30,2.0:30,3.0:40"
            )
            from app.services.risk_manager import RiskManager
            rm = RiskManager()
            rm.entry_prices = {"BTCUSDT": 50000.0}
            return rm

    def test_should_check_trailing_tp_enabled(self, risk_manager):
        """Test trailing TP check when enabled and position exists."""
        result = risk_manager.should_check_trailing_tp("BTCUSDT")
        assert result == True

    def test_should_check_trailing_tp_no_position(self, risk_manager):
        """Test trailing TP check when no position exists."""
        result = risk_manager.should_check_trailing_tp("ETHUSDT")
        assert result == False

    def test_activate_trailing_tp(self, risk_manager):
        """Test trailing TP activation when profit threshold is reached."""
        # Price goes from 50000 to 50800 (1.6% gain - above 1.5% activation)
        risk_manager.activate_trailing_tp("BTCUSDT", 50800.0, atr=200.0)

        assert risk_manager.trailing_tp_state["BTCUSDT"]["is_active"] == True
        assert risk_manager.trailing_tp_state["BTCUSDT"]["highest_price"] == 50800.0

    def test_activate_trailing_tp_below_threshold(self, risk_manager):
        """Test trailing TP not activated when profit is below threshold."""
        # Price goes from 50000 to 50500 (1.0% gain - below 1.5% activation)
        risk_manager.activate_trailing_tp("BTCUSDT", 50500.0, atr=200.0)

        # Should not create state or should be inactive
        if "BTCUSDT" in risk_manager.trailing_tp_state:
            assert risk_manager.trailing_tp_state["BTCUSDT"]["is_active"] == False
        # If key doesn't exist, that's also correct (not activated)

    def test_update_trailing_tp_new_high(self, risk_manager):
        """Test trailing TP updates when price makes new high."""
        # First activate
        risk_manager.activate_trailing_tp("BTCUSDT", 50800.0, atr=200.0)

        # Then price goes higher
        risk_manager.update_trailing_tp("BTCUSDT", 51200.0, atr=200.0)

        assert risk_manager.trailing_tp_state["BTCUSDT"]["highest_price"] == 51200.0
        # trailing_level should be 51200 - (200 * 2) = 50800
        assert risk_manager.trailing_tp_state["BTCUSDT"]["trailing_level"] == 50800.0

    def test_trailing_tp_triggered(self, risk_manager):
        """Test trailing TP triggers when price falls below trailing level."""
        # Activate with high price
        risk_manager.activate_trailing_tp("BTCUSDT", 52000.0, atr=200.0)
        # Update to new high
        risk_manager.update_trailing_tp("BTCUSDT", 53000.0, atr=200.0)
        # trailing_level = 53000 - 400 = 52600

        # Price falls below trailing level
        result = risk_manager.check_trailing_tp("BTCUSDT", 52500.0)

        assert result is not None
        assert result["signal"] == "TRAILING_TP"
        assert result["is_final"] == True
        assert risk_manager.trailing_tp_state["BTCUSDT"]["is_active"] == False

    def test_trailing_tp_not_triggered(self, risk_manager):
        """Test trailing TP doesn't trigger when price stays above trailing level."""
        risk_manager.activate_trailing_tp("BTCUSDT", 52000.0, atr=200.0)
        risk_manager.update_trailing_tp("BTCUSDT", 53000.0, atr=200.0)

        # Price is still above trailing level (52600)
        result = risk_manager.check_trailing_tp("BTCUSDT", 52800.0)

        assert result is None


class TestTimeBasedExit:
    """Tests for Time-Based Exit functionality."""

    @pytest.fixture
    def risk_manager_with_settings(self):
        """Create risk manager and patch settings directly."""
        import app.services.risk_manager as rm_module

        # Patch settings module-level
        mock_settings = MagicMock(
            ENABLE_TRAILING_TP=False,
            TRAILING_TP_ATR_MULTIPLIER=2.0,
            TRAILING_TP_ACTIVATION_PCT=1.5,
            ENABLE_TIME_EXIT=True,
            MAX_HOLD_HOURS=4,
            TIME_EXIT_COOLDOWN_MINUTES=15,
            ENABLE_SIGNAL_STRENGTH_EXIT=False,
            ENABLE_DYNAMIC_PARTIAL_TP=True,
            STOP_LOSS_PCT=2.0,
            ALLOCATED_CAPITAL=1000,
            RISK_PER_TRADE_PCT=1.0,
            PARTIAL_TP_LEVELS="1.0:30,2.0:30,3.0:40"
        )
        rm_module.settings = mock_settings
        return rm_module.RiskManager()

    @pytest.fixture
    def risk_manager_disabled(self):
        """Create risk manager with time exit disabled."""
        import app.services.risk_manager as rm_module

        mock_settings = MagicMock(
            ENABLE_TRAILING_TP=False,
            TRAILING_TP_ATR_MULTIPLIER=2.0,
            TRAILING_TP_ACTIVATION_PCT=1.5,
            ENABLE_TIME_EXIT=False,
            MAX_HOLD_HOURS=4,
            TIME_EXIT_COOLDOWN_MINUTES=15,
            ENABLE_SIGNAL_STRENGTH_EXIT=False,
            ENABLE_DYNAMIC_PARTIAL_TP=True,
            STOP_LOSS_PCT=2.0,
            ALLOCATED_CAPITAL=1000,
            RISK_PER_TRADE_PCT=1.0,
            PARTIAL_TP_LEVELS="1.0:30,2.0:30,3.0:40"
        )
        rm_module.settings = mock_settings
        return rm_module.RiskManager()

    def test_should_check_time_exit_disabled(self, risk_manager_disabled):
        """Test time exit check when disabled."""
        risk_manager_disabled.position_data["BTCUSDT"] = {"current_qty": 0.1}
        result = risk_manager_disabled.should_check_time_exit("BTCUSDT")
        assert result == False

    def test_check_time_exit_within_limit(self, risk_manager_with_settings):
        """Test time exit doesn't trigger when within time limit."""
        from datetime import datetime, timezone, timedelta

        risk_manager_with_settings.entry_prices["BTCUSDT"] = 50000.0
        risk_manager_with_settings.position_data["BTCUSDT"] = {
            "current_qty": 0.1,
            "entry_time": datetime.now(timezone.utc) - timedelta(hours=2),  # 2 hours ago
            "current_price": 51000.0
        }

        result = risk_manager_with_settings.check_time_exit("BTCUSDT")

        assert result is None

    def test_check_time_exit_exceeds_limit(self, risk_manager_with_settings):
        """Test time exit triggers when time limit exceeded."""
        from datetime import datetime, timezone, timedelta

        risk_manager_with_settings.entry_prices["BTCUSDT"] = 50000.0
        risk_manager_with_settings.position_data["BTCUSDT"] = {
            "current_qty": 0.1,
            "entry_time": datetime.now(timezone.utc) - timedelta(hours=5),  # 5 hours ago
            "current_price": 51000.0
        }

        result = risk_manager_with_settings.check_time_exit("BTCUSDT")

        assert result is not None
        assert result["signal"] == "TIME_EXIT"
        assert result["is_final"] == True


class TestSignalStrength:
    """Tests for Signal Strength classification."""

    @pytest.fixture
    def risk_manager(self):
        with patch('app.services.risk_manager.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                ENABLE_TRAILING_TP=False,
                TRAILING_TP_ATR_MULTIPLIER=2.0,
                TRAILING_TP_ACTIVATION_PCT=1.5,
                ENABLE_TIME_EXIT=False,
                MAX_HOLD_HOURS=4,
                TIME_EXIT_COOLDOWN_MINUTES=15,
                ENABLE_SIGNAL_STRENGTH_EXIT=True,
                ENABLE_DYNAMIC_PARTIAL_TP=True,
                STOP_LOSS_PCT=2.0,
                ALLOCATED_CAPITAL=1000,
                RISK_PER_TRADE_PCT=1.0,
                PARTIAL_TP_LEVELS="1.0:30,2.0:30,3.0:40"
            )
            from app.services.risk_manager import RiskManager
            return RiskManager()

    def test_signal_strength_strong_buy(self, risk_manager):
        """Test STRONG signal classification - deeply oversold."""
        # RSI = 15, oversold threshold = 30
        # distance = 30 - 15 = 15 >= 10 -> STRONG
        result = risk_manager.classify_signal_strength(15.0, 30.0, "buy")
        assert result == "STRONG"

    def test_signal_strength_moderate_buy(self, risk_manager):
        """Test MODERATE signal classification - near oversold threshold."""
        # RSI = 25, oversold threshold = 30
        # distance = 30 - 25 = 5 >= 5 but < 10 -> MODERATE
        result = risk_manager.classify_signal_strength(25.0, 30.0, "buy")
        assert result == "MODERATE"

    def test_signal_strength_weak_buy(self, risk_manager):
        """Test WEAK signal classification - barely oversold."""
        # RSI = 27, oversold threshold = 30
        # distance = 30 - 27 = 3 < 5 -> WEAK
        result = risk_manager.classify_signal_strength(27.0, 30.0, "buy")
        assert result == "WEAK"

    def test_signal_strength_strong_sell(self, risk_manager):
        """Test STRONG signal classification - deeply overbought."""
        # RSI = 85, overbought threshold = 70
        # distance = 85 - 70 = 15 >= 10 -> STRONG
        result = risk_manager.classify_signal_strength(85.0, 70.0, "sell")
        assert result == "STRONG"

    def test_get_adjusted_exit_threshold_strong(self, risk_manager):
        """Test exit threshold adjustment for STRONG signal."""
        risk_manager.position_data["BTCUSDT"] = {"signal_strength": "STRONG"}
        result = risk_manager.get_adjusted_exit_threshold("BTCUSDT", 70.0, "sell")
        assert result == 70.0  # No adjustment

    def test_get_adjusted_exit_threshold_moderate(self, risk_manager):
        """Test exit threshold adjustment for MODERATE signal."""
        risk_manager.position_data["BTCUSDT"] = {"signal_strength": "MODERATE"}
        result = risk_manager.get_adjusted_exit_threshold("BTCUSDT", 70.0, "sell")
        assert result == 65.0  # -5

    def test_get_adjusted_exit_threshold_weak(self, risk_manager):
        """Test exit threshold adjustment for WEAK signal."""
        risk_manager.position_data["BTCUSDT"] = {"signal_strength": "WEAK"}
        result = risk_manager.get_adjusted_exit_threshold("BTCUSDT", 70.0, "sell")
        assert result == 60.0  # -10


class TestDynamicPartialTP:
    """Tests for Dynamic Partial Take Profit."""

    @pytest.fixture
    def risk_manager(self):
        with patch('app.services.risk_manager.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                ENABLE_TRAILING_TP=False,
                TRAILING_TP_ATR_MULTIPLIER=2.0,
                TRAILING_TP_ACTIVATION_PCT=1.5,
                ENABLE_TIME_EXIT=False,
                MAX_HOLD_HOURS=4,
                TIME_EXIT_COOLDOWN_MINUTES=15,
                ENABLE_SIGNAL_STRENGTH_EXIT=False,
                ENABLE_DYNAMIC_PARTIAL_TP=True,
                STOP_LOSS_PCT=2.0,
                ALLOCATED_CAPITAL=1000,
                RISK_PER_TRADE_PCT=1.0,
                PARTIAL_TP_LEVELS="1.0:30,2.0:30,3.0:40"
            )
            from app.services.risk_manager import RiskManager
            return RiskManager()

    def test_dynamic_tp_high_volatility(self, risk_manager):
        """Test dynamic TP levels for high volatility (ATR > 2%)."""
        # ATR% = 3.0%
        levels = risk_manager.get_dynamic_tp_levels("BTCUSDT", 50000.0, 3.0)

        # volatility_multiplier = 1 + (3.0 - 2) * 0.3 = 1.3
        # Level 1: 1.0 * 1.3 = 1.3
        # Level 2: 2.0 * 1.3 = 2.6
        # Level 3: 3.0 * 1.3 = 3.9
        assert len(levels) == 3
        assert abs(levels[0][0] - 1.3) < 0.01
        assert abs(levels[1][0] - 2.6) < 0.01
        assert abs(levels[2][0] - 3.9) < 0.01

    def test_dynamic_tp_low_volatility(self, risk_manager):
        """Test dynamic TP levels for low volatility (ATR <= 1%)."""
        # ATR% = 0.8%
        levels = risk_manager.get_dynamic_tp_levels("BTCUSDT", 50000.0, 0.8)

        # volatility_multiplier = 0.8
        # Level 1: 1.0 * 0.8 = 0.8
        assert len(levels) == 3
        assert abs(levels[0][0] - 0.8) < 0.01

    def test_dynamic_tp_normal_volatility(self, risk_manager):
        """Test dynamic TP levels for normal volatility (1% < ATR <= 2%)."""
        # ATR% = 1.5%
        levels = risk_manager.get_dynamic_tp_levels("BTCUSDT", 50000.0, 1.5)

        # volatility_multiplier = 1.0 (no adjustment)
        # Level 1: 1.0 * 1.0 = 1.0
        assert len(levels) == 3
        assert abs(levels[0][0] - 1.0) < 0.01


class TestRSIDivergenceExit:
    """Tests for RSI Divergence Exit."""

    @pytest.fixture
    def risk_manager(self):
        """Create risk manager with signal strength exit enabled."""
        import app.services.risk_manager as rm_module

        mock_settings = MagicMock(
            ENABLE_TRAILING_TP=False,
            TRAILING_TP_ATR_MULTIPLIER=2.0,
            TRAILING_TP_ACTIVATION_PCT=1.5,
            ENABLE_TIME_EXIT=False,
            MAX_HOLD_HOURS=4,
            TIME_EXIT_COOLDOWN_MINUTES=15,
            ENABLE_SIGNAL_STRENGTH_EXIT=True,
            ENABLE_DYNAMIC_PARTIAL_TP=True,
            STOP_LOSS_PCT=2.0,
            ALLOCATED_CAPITAL=1000,
            RISK_PER_TRADE_PCT=1.0,
            PARTIAL_TP_LEVELS="1.0:30,2.0:30,3.0:40"
        )
        rm_module.settings = mock_settings
        return rm_module.RiskManager()

    @patch('app.services.indicators.get_symbol_data')
    def test_check_divergence_exit_bearish(self, mock_get_symbol, risk_manager):
        """Test divergence exit when bearish divergence detected."""
        mock_symbol_data = MagicMock()
        mock_symbol_data.get_divergence.return_value = "bearish_divergence"
        mock_symbol_data.closes = [50000.0, 51000.0, 52000.0]
        mock_get_symbol.return_value = mock_symbol_data

        risk_manager.entry_prices["BTCUSDT"] = 50000.0
        risk_manager.position_data["BTCUSDT"] = {"current_qty": 0.1}

        result = risk_manager.check_divergence_exit("BTCUSDT")

        assert result is not None
        assert result["signal"] == "DIVERGENCE_EXIT"

    @patch('app.services.indicators.get_symbol_data')
    def test_check_divergence_exit_no_divergence(self, mock_get_symbol, risk_manager):
        """Test divergence exit when no divergence."""
        mock_symbol_data = MagicMock()
        mock_symbol_data.get_divergence.return_value = "bullish_divergence"
        mock_get_symbol.return_value = mock_symbol_data

        risk_manager.entry_prices["BTCUSDT"] = 50000.0
        risk_manager.position_data["BTCUSDT"] = {"current_qty": 0.1}

        result = risk_manager.check_divergence_exit("BTCUSDT")

        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])