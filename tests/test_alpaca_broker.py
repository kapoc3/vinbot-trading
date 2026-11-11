import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from app.services.brokers.base import BaseBrokerAdapter
from app.services.brokers.alpaca_adapter import AlpacaAdapter
from app.services.brokers.binance_adapter import BinanceAdapter
from app.services.brokers import get_broker_adapter
from app.services.alpaca_client import AlpacaClient


def test_base_broker_adapter_abstract():
    """Verify BaseBrokerAdapter cannot be instantiated directly without implementing abstract methods."""
    with pytest.raises(TypeError):
        BaseBrokerAdapter()


def test_alpaca_adapter_get_account():
    """Test AlpacaAdapter.get_account() normalization."""
    adapter = AlpacaAdapter()

    fake_alpaca_acc = {
        "id": "acc-12345",
        "equity": "25000.50",
        "cash": "10000.25",
        "buying_power": "50000.00",
        "status": "ACTIVE",
        "currency": "USD",
    }

    async def _run():
        with patch("app.services.brokers.alpaca_adapter.alpaca_client.get_account", new_callable=AsyncMock) as mock_get_acc:
            mock_get_acc.return_value = fake_alpaca_acc
            res = await adapter.get_account()

            assert res["equity_usd"] == 25000.50
            assert res["cash_usd"] == 10000.25
            assert res["buying_power_usd"] == 50000.00
            assert res["currency"] == "USD"
            assert res["status"] == "ACTIVE"
            assert res["is_paper"] is True

    asyncio.run(_run())


def test_alpaca_adapter_get_wallet_balances():
    """Test AlpacaAdapter.get_wallet_balances() builds synthesized assets list."""
    adapter = AlpacaAdapter()

    fake_acc = {
        "equity": "15000.00",
        "cash": "5000.00",
        "buying_power": "10000.00",
        "status": "ACTIVE",
    }
    fake_positions = [
        {
            "symbol": "SPY",
            "qty": "10",
            "current_price": "500.00",
            "avg_entry_price": "490.00",
            "market_value": "5000.00",
            "unrealized_plpc": "0.0204",
        },
        {
            "symbol": "BTC/USD",
            "qty": "0.1",
            "current_price": "50000.00",
            "avg_entry_price": "48000.00",
            "market_value": "5000.00",
            "unrealized_plpc": "0.0416",
        }
    ]

    async def _run():
        with patch.object(adapter, "get_account", new_callable=AsyncMock) as mock_get_acc, \
             patch("app.services.brokers.alpaca_adapter.alpaca_client.get_positions", new_callable=AsyncMock) as mock_get_pos:
            mock_get_acc.return_value = {
                "equity_usd": 15000.00,
                "cash_usd": 5000.00,
                "buying_power_usd": 10000.00,
                "currency": "USD",
                "is_paper": True,
                "status": "ACTIVE",
            }
            mock_get_pos.return_value = fake_positions

            balances = await adapter.get_wallet_balances()
            assert len(balances) == 3
            # Cash asset
            usd_asset = next(b for b in balances if b["asset"] == "USD")
            assert usd_asset["free"] == 5000.00
            assert usd_asset["is_stable"] is True

            # SPY asset
            spy_asset = next(b for b in balances if b["asset"] == "SPY")
            assert spy_asset["free"] == 10.0
            assert spy_asset["price_usd"] == 500.00
            assert spy_asset["entry_price"] == 490.00
            assert spy_asset["in_bot_position"] is True
            assert spy_asset["unrealized_pnl_pct"] == 2.04

    asyncio.run(_run())


def test_alpaca_adapter_get_positions():
    """Test AlpacaAdapter.get_positions() normalization."""
    adapter = AlpacaAdapter()

    fake_positions = [
        {
            "symbol": "AAPL",
            "qty": "15",
            "avg_entry_price": "220.00",
            "current_price": "230.00",
            "unrealized_pl": "150.00",
            "unrealized_plpc": "0.0454",
            "market_value": "3450.00",
            "side": "long"
        }
    ]

    async def _run():
        with patch("app.services.brokers.alpaca_adapter.alpaca_client.get_positions", new_callable=AsyncMock) as mock_pos:
            mock_pos.return_value = fake_positions
            positions = await adapter.get_positions()
            assert len(positions) == 1
            p = positions[0]
            assert p["symbol"] == "AAPL"
            assert p["qty"] == 15.0
            assert p["entry_price"] == 220.0
            assert p["current_price"] == 230.0
            assert p["unrealized_pnl_usd"] == 150.0
            assert p["unrealized_pnl_pct"] == 4.54
            assert p["market_value_usd"] == 3450.0
            assert p["side"] == "long"

    asyncio.run(_run())


def test_alpaca_adapter_place_order_bracket():
    """Test AlpacaAdapter.place_order() with bracket parameters."""
    adapter = AlpacaAdapter()

    mock_raw_order = {
        "id": "order-alp-999",
        "client_order_id": "vinbot-bracket-1",
        "symbol": "NVDA",
        "side": "buy",
        "status": "accepted",
        "filled_qty": "0",
        "filled_avg_price": None
    }

    async def _run():
        with patch("app.services.brokers.alpaca_adapter.alpaca_client.place_order", new_callable=AsyncMock) as mock_place:
            mock_place.return_value = mock_raw_order
            res = await adapter.place_order(
                symbol="NVDA",
                side="BUY",
                quantity=2.0,
                order_type="MARKET",
                take_profit_price=150.0,
                stop_loss_price=120.0
            )

            mock_place.assert_called_once_with(
                symbol="NVDA",
                side="BUY",
                qty=2.0,
                order_type="MARKET",
                time_in_force="gtc",
                take_profit_price=150.0,
                stop_loss_price=120.0,
                limit_price=None,
            )

            assert res["orderId"] == "order-alp-999"
            assert res["clientOrderId"] == "vinbot-bracket-1"
            assert res["symbol"] == "NVDA"
            assert res["side"] == "BUY"
            assert res["status"] == "ACCEPTED"

    asyncio.run(_run())


def test_alpaca_client_bracket_payload():
    """Test AlpacaClient builds native bracket order payload."""
    client = AlpacaClient()

    async def _run():
        with patch.object(client, "request_trading", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"id": "ord-123"}
            await client.place_order(
                symbol="SPY",
                side="BUY",
                qty=5.0,
                order_type="market",
                time_in_force="gtc",
                take_profit_price=530.00,
                stop_loss_price=510.00,
            )

            mock_req.assert_called_once()
            args, kwargs = mock_req.call_args
            assert args[0] == "POST"
            assert args[1] == "/v2/orders"
            payload = kwargs["json_data"]
            assert payload["symbol"] == "SPY"
            assert payload["qty"] == "5.0"
            assert payload["side"] == "buy"
            assert payload["type"] == "market"
            assert payload["order_class"] == "bracket"
            assert payload["take_profit"] == {"limit_price": "530.0"}
            assert payload["stop_loss"] == {"stop_price": "510.0"}

    asyncio.run(_run())


def test_broker_factory_selection():
    """Test get_broker_adapter() factory dynamically switches adapters."""
    alpaca_adapter = get_broker_adapter("alpaca")
    assert isinstance(alpaca_adapter, AlpacaAdapter)
    assert alpaca_adapter.broker_name == "alpaca"

    binance_adapter = get_broker_adapter("binance")
    assert isinstance(binance_adapter, BinanceAdapter)
    assert binance_adapter.broker_name == "binance"


def test_dashboard_broker_status_endpoint():
    """Test GET /api/v1/dashboard/broker/status endpoint returns active broker info."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api.v1.endpoints.dashboard import verify_session

    client = TestClient(app)
    app.dependency_overrides[verify_session] = lambda: "admin"

    with patch("app.services.brokers.alpaca_adapter.alpaca_client.get_account", new_callable=AsyncMock) as mock_acc:
        mock_acc.return_value = {
            "equity": "25000.00",
            "cash": "10000.00",
            "buying_power": "40000.00",
            "status": "ACTIVE",
        }
        res = client.get("/api/v1/dashboard/broker/status")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "broker" in data
        assert "backend" in data
        assert "account" in data

    app.dependency_overrides.clear()

