import pytest
from unittest.mock import AsyncMock, patch
from app.core.config import Settings, get_settings
from app.services.risk_manager import RiskManager


def test_fee_config_properties():
    # 1. Standard 0.10% fee (no BNB discount)
    s_std = Settings(BINANCE_FEE_PCT=0.1, USE_BNB_FEE_DISCOUNT=False)
    assert s_std.EFFECTIVE_FEE_PCT == 0.1
    # (1 + 0.001) / (1 - 0.001) = 1.002002002...
    assert round(s_std.ROUND_TRIP_FEE_FACTOR, 6) == 1.002002

    # 2. With 25% BNB fee discount (0.075% fee)
    s_bnb = Settings(BINANCE_FEE_PCT=0.1, USE_BNB_FEE_DISCOUNT=True)
    assert s_bnb.EFFECTIVE_FEE_PCT == 0.075
    # (1 + 0.00075) / (1 - 0.00075) = 1.001501125...
    assert round(s_bnb.ROUND_TRIP_FEE_FACTOR, 6) == 1.001501


def test_calculate_net_trade_pnl():
    rm = RiskManager()
    entry_p = 100.0
    qty = 1.0  # $100 notional

    # Flat sale at entry price (0 gross gain)
    gross, fee, net = rm.calculate_net_trade_pnl(entry_price=entry_p, exit_price=entry_p, quantity=qty)
    assert gross == 0.0
    assert fee > 0.0
    assert net == -fee  # Net loss equals exact commissions paid

    # Sale at Break-Even factor
    settings = get_settings()
    be_exit = entry_p * settings.ROUND_TRIP_FEE_FACTOR
    gross_be, fee_be, net_be = rm.calculate_net_trade_pnl(entry_price=entry_p, exit_price=be_exit, quantity=qty)
    assert gross_be > 0
    # Net PnL must be >= 0.00 (within floating point precision)
    assert round(net_be, 2) >= 0.00


@pytest.mark.anyio
async def test_move_sl_to_be_plus_fees():
    rm = RiskManager()
    symbol = "SOLUSDC"
    entry_p = 200.0
    qty = 0.5

    with patch("app.services.risk_manager.persistence.set_state", new_callable=AsyncMock):
        await rm.set_entry_price(symbol, entry_p, quantity=qty)
        assert rm.entry_prices[symbol] == entry_p

        # Simulate Partial TP 1 hit
        await rm.update_partial_execution(symbol, executed_qty=0.25)
        
        pos_meta = rm.position_data[symbol]
        settings = get_settings()

        expected_be_sl = entry_p * settings.ROUND_TRIP_FEE_FACTOR
        assert round(pos_meta["sl_price"], 4) == round(expected_be_sl, 4)
        # The new SL is strictly above the original entry price
        assert pos_meta["sl_price"] > entry_p


def test_take_profit_net_vs_gross():
    rm = RiskManager()
    symbol = "BTCUSDC"
    entry_p = 100.0
    qty = 1.0

    rm.entry_prices[symbol] = entry_p
    rm.position_data[symbol] = {
        "initial_qty": qty,
        "current_qty": qty,
        "tp_hits": 0,
        "sl_price": 98.0,
    }

    # Mock TP targets: TP1 = 1.0% net, TP2 = 2.0% net
    rm._get_tp_targets = lambda: [(1.0, 0.5), (2.0, 0.5)]

    # If price rises by only +0.95% (e.g. 100.95), gross is 0.95%, but net after fees is < 1.0%
    res_under = rm.check_sl_tp(symbol, current_price=100.95)
    assert res_under is None  # Should NOT trigger TP prematurely

    # When price rises to 101.20 (enough to clear the 1.0% target + round-trip fee)
    res_hit = rm.check_sl_tp(symbol, current_price=101.20)
    assert res_hit is not None
    assert res_hit["signal"] == "PARTIAL_TP"
    assert res_hit["pnl"] >= 1.0  # Net PnL is at least 1.0%
