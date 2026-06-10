"""
Tests for Portfolio Rebalancing.
"""
import pytest
from unittest.mock import MagicMock, patch
import numpy as np


class TestEqualAllocator:
    """Tests for equal weight allocator."""

    def test_equal_allocation(self):
        """Test equal weight across symbols."""
        from app.services.portfolio.allocator import EqualAllocator

        allocator = EqualAllocator()
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        weights = allocator.allocate(symbols, {})

        for symbol in symbols:
            assert abs(weights[symbol] - 33.33) < 0.1

    def test_empty_symbols(self):
        """Test empty symbols returns empty dict."""
        from app.services.portfolio.allocator import EqualAllocator

        allocator = EqualAllocator()
        weights = allocator.allocate([], {})

        assert weights == {}


class TestVolatilityAllocator:
    """Tests for volatility-based allocator."""

    def test_inverse_volatility_allocation(self):
        """Test inverse volatility weighting."""
        from app.services.portfolio.allocator import VolatilityAllocator

        allocator = VolatilityAllocator()

        # Mock SymbolData
        symbol_data = {
            "BTCUSDT": MagicMock(
                closes=[100 + i for i in range(50)],
                highs=[105 + i for i in range(50)],
                lows=[95 + i for i in range(50)]
            ),
            "ETHUSDT": MagicMock(
                closes=[2000 + i * 2 for i in range(50)],
                highs=[2010 + i * 2 for i in range(50)],
                lows=[1990 + i * 2 for i in range(50)]
            )
        }

        symbols = ["BTCUSDT", "ETHUSDT"]
        weights = allocator.allocate(symbols, symbol_data)

        assert "BTCUSDT" in weights
        assert "ETHUSDT" in weights
        assert abs(sum(weights.values()) - 100) < 0.1

    def test_default_weight_for_missing_data(self):
        """Test default weight when data insufficient."""
        from app.services.portfolio.allocator import VolatilityAllocator

        allocator = VolatilityAllocator()
        symbols = ["BTCUSDT", "ETHUSDT"]
        weights = allocator.allocate(symbols, {})

        # Both should have equal weight
        assert weights["BTCUSDT"] == weights["ETHUSDT"]


class TestRiskWeightedAllocator:
    """Tests for risk-weighted allocator."""

    def test_risk_allocation(self):
        """Test risk-based allocation returns valid weights."""
        from app.services.portfolio.allocator import RiskWeightedAllocator

        allocator = RiskWeightedAllocator()

        symbol_data = {
            "BTCUSDT": MagicMock(closes=[100 + i for i in range(50)]),
            "ETHUSDT": MagicMock(closes=[2000 + i for i in range(50)])
        }

        symbols = ["BTCUSDT", "ETHUSDT"]
        weights = allocator.allocate(symbols, symbol_data)

        assert abs(sum(weights.values()) - 100) < 0.1
        assert weights["BTCUSDT"] > 0
        assert weights["ETHUSDT"] > 0


class TestPortfolioRebalancer:
    """Tests for portfolio rebalancer."""

    @patch("app.services.portfolio.allocator.settings")
    def test_rebalance_check_needed(self, mock_settings):
        """Test rebalance check when deviation exceeds threshold."""
        mock_settings.PORTFOLIO_REBALANCING_ENABLED = True
        mock_settings.ALLOCATION_METHOD = "equal"
        mock_settings.REBALANCE_THRESHOLD_PCT = 20.0

        from app.services.portfolio.allocator import PortfolioRebalancer

        rebalancer = PortfolioRebalancer()
        rebalancer.current_allocation = {"BTCUSDT": 30.0, "ETHUSDT": 70.0}

        # Current: BTC=50%, ETH=50% - deviation for BTC is 66%
        current_positions = {"BTCUSDT": 5000, "ETHUSDT": 5000}
        total_value = 10000

        targets = rebalancer.check_rebalance_needed(current_positions, total_value)

        btc_target = next(t for t in targets if t.symbol == "BTCUSDT")
        assert btc_target.action == "DECREASE"
        assert btc_target.deviation_pct > 20

    @patch("app.services.portfolio.allocator.settings")
    def test_rebalance_not_needed(self, mock_settings):
        """Test no rebalance when within threshold."""
        mock_settings.PORTFOLIO_REBALANCING_ENABLED = True
        mock_settings.ALLOCATION_METHOD = "equal"
        mock_settings.REBALANCE_THRESHOLD_PCT = 20.0

        from app.services.portfolio.allocator import PortfolioRebalancer

        rebalancer = PortfolioRebalancer()
        rebalancer.current_allocation = {"BTCUSDT": 50.0, "ETHUSDT": 50.0}

        # Current: BTC=48%, ETH=52% - deviation ~4%
        current_positions = {"BTCUSDT": 4800, "ETHUSDT": 5200}
        total_value = 10000

        targets = rebalancer.check_rebalance_needed(current_positions, total_value)

        for t in targets:
            assert t.action == "HOLD"

    def test_position_size_calculation(self):
        """Test position size calculation."""
        from app.services.portfolio.allocator import PortfolioRebalancer

        rebalancer = PortfolioRebalancer()
        rebalancer.current_allocation = {"BTCUSDT": 30.0}

        size = rebalancer.get_position_size("BTCUSDT", 10000)
        assert size == 3000.0


class TestPortfolioConfig:
    """Tests for portfolio configuration."""

    def test_portfolio_config_defaults(self):
        """Test portfolio config has correct defaults."""
        from app.core.config import get_settings

        settings = get_settings()

        assert settings.PORTFOLIO_REBALANCING_ENABLED is False
        assert settings.ALLOCATION_METHOD == "equal"
        assert settings.REBALANCE_THRESHOLD_PCT == 20.0
        assert settings.MAX_POSITION_PCT == 30.0
        assert settings.MIN_POSITION_PCT == 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])