import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

@pytest.fixture
def mock_dependencies():
    with patch("app.api.v1.endpoints.dashboard.trading_engine") as mock_engine, \
         patch("app.api.v1.endpoints.dashboard.risk_manager") as mock_risk, \
         patch("app.api.v1.endpoints.dashboard.statistics_service") as mock_stats, \
         patch("app.api.v1.endpoints.dashboard.regime_service") as mock_regime, \
         patch("app.api.v1.endpoints.dashboard.strategy_manager") as mock_strat, \
         patch("app.api.v1.endpoints.dashboard.db") as mock_db, \
         patch("app.api.v1.endpoints.dashboard.settings") as mock_settings:
         
        # Default mock returns
        mock_engine.is_running = True
        mock_risk.daily_pnl = 15.5
        mock_risk.is_trading_allowed.return_value = True
        mock_risk.reset_daily_stats = AsyncMock()
        mock_risk.clear_entry_price = AsyncMock()
        
        mock_stats.get_all_symbols_stats = AsyncMock(return_value={"total_profit": 120.45})
        mock_settings.TRADING_SYMBOLS = "BTCUSDT,ETHUSDT"
        mock_settings.TRADING_STRATEGY = "RSIStrategy"
        mock_settings.DASHBOARD_USERNAME = "admin"
        mock_settings.DASHBOARD_PASSWORD = "admin"
        mock_settings.SECRET_KEY = "secret"
        
        from app.services.regime_service import MarketRegime
        mock_regime.current_regimes = {
            "BTCUSDT": MarketRegime.TRENDING,
            "ETHUSDT": MarketRegime.RANGING
        }
        
        mock_strat.get_strategy.return_value = MagicMock(__class__=MagicMock(__name__="RSIStrategy"))
        
        # Mock DB select for recent trades
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [
            {
                "order_id": 12345,
                "symbol": "BTCUSDT",
                "side": "BUY",
                "price": 60000.0,
                "quantity": 0.05,
                "rsi": 25.4,
                "timestamp": "2026-06-10 00:00:00"
            }
        ]
        mock_db.execute = AsyncMock(return_value=mock_cursor)
        
        yield {
            "engine": mock_engine,
            "risk": mock_risk,
            "stats": mock_stats,
            "regime": mock_regime,
            "strat": mock_strat,
            "db": mock_db,
            "settings": mock_settings
        }

def test_dashboard_endpoint_requires_auth(mock_dependencies):
    from app.main import app
    client = TestClient(app)
    
    # Request without auth cookie should fail
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 401

def test_dashboard_login_logout_flow(mock_dependencies):
    from app.main import app
    client = TestClient(app)
    
    # 1. Login with bad credentials
    response = client.post("/api/v1/dashboard/login", json={"username": "admin", "password": "wrongpassword"})
    assert response.status_code == 401
    
    # 2. Login with correct credentials
    response = client.post("/api/v1/dashboard/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    assert "session_token" in client.cookies
    
    # 3. Request data with valid session
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    assert response.json()["bot_running"] is True
    
    # 4. Logout
    response = client.post("/api/v1/dashboard/logout")
    assert response.status_code == 200
    assert "session_token" not in client.cookies

def test_dashboard_endpoint_success_with_override(mock_dependencies):
    from app.main import app
    from app.api.v1.endpoints.dashboard import _cache, verify_session
    
    # Override auth dependency
    app.dependency_overrides[verify_session] = lambda: "admin"
    
    # Reset cache before test
    _cache["data"] = None
    _cache["timestamp"] = 0.0
    
    client = TestClient(app)
    response = client.get("/api/v1/dashboard")
    
    assert response.status_code == 200
    data = response.json()
    assert data["bot_running"] is True
    assert data["daily_pnl"] == 15.5
    assert data["accumulated_pnl"] == 120.45
    assert data["allowed_to_trade"] is True
    assert data["strategy_mode"] == "RSIStrategy"
    assert data["symbol_regimes"] == {"BTCUSDT": "Trending", "ETHUSDT": "Ranging"}
    
    # Clean overrides
    app.dependency_overrides.clear()

def test_dashboard_endpoint_caching(mock_dependencies):
    from app.main import app
    from app.api.v1.endpoints.dashboard import _cache, verify_session
    
    app.dependency_overrides[verify_session] = lambda: "admin"
    
    # Reset cache
    _cache["data"] = None
    _cache["timestamp"] = 0.0
    
    client = TestClient(app)
    
    # First request
    response1 = client.get("/api/v1/dashboard")
    assert response1.status_code == 200
    time1 = response1.json()["timestamp"]
    
    # Modify mock value to see if cache is returned
    mock_dependencies["risk"].daily_pnl = 999.9
    
    # Second request (immediate, should hit cache)
    response2 = client.get("/api/v1/dashboard")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["timestamp"] == time1
    assert data2["daily_pnl"] == 15.5  # Old value from cache
    
    # Fast forward cache duration
    with patch("time.time", return_value=time.time() + 6.0):
        response3 = client.get("/api/v1/dashboard")
        assert response3.status_code == 200
        data3 = response3.json()
        assert data3["timestamp"] > time1
        assert data3["daily_pnl"] == 999.9  # New value fetched
        
    app.dependency_overrides.clear()

def test_dashboard_control_actions(mock_dependencies):
    from app.main import app
    from app.api.v1.endpoints.dashboard import verify_session
    from app.services.strategy_factory import current_strategy
    
    app.dependency_overrides[verify_session] = lambda: "admin"
    client = TestClient(app)
    
    # 1. Test Bot Stop
    response = client.post("/api/v1/dashboard/bot/stop")
    assert response.status_code == 200
    assert mock_dependencies["engine"].is_running is False
    
    # 2. Test Bot Start
    response = client.post("/api/v1/dashboard/bot/start")
    assert response.status_code == 200
    assert mock_dependencies["engine"].is_running is True
    
    # 3. Test Reset Operations
    with patch.object(current_strategy, "update_position", new_callable=AsyncMock) as mock_update_pos:
        response = client.post("/api/v1/dashboard/reset-operations")
        assert response.status_code == 200
        mock_dependencies["risk"].reset_daily_stats.assert_called_once()
        mock_dependencies["risk"].clear_entry_price.assert_any_call("BTCUSDT")
        mock_dependencies["risk"].clear_entry_price.assert_any_call("ETHUSDT")
        mock_update_pos.assert_any_call("BTCUSDT", False)
        mock_update_pos.assert_any_call("ETHUSDT", False)
        
    app.dependency_overrides.clear()

def test_dashboard_get_trades_endpoint(mock_dependencies):
    from app.main import app
    from app.api.v1.endpoints.dashboard import verify_session
    
    app.dependency_overrides[verify_session] = lambda: "admin"
    client = TestClient(app)
    
    # 1. Test get all trades without date filter
    response = client.get("/api/v1/dashboard/trades")
    assert response.status_code == 200
    trades = response.json()
    assert len(trades) == 1
    assert trades[0]["symbol"] == "BTCUSDT"
    
    # 2. Test get trades with valid date
    response = client.get("/api/v1/dashboard/trades?date=2026-06-10")
    assert response.status_code == 200
    mock_dependencies["db"].execute.assert_called_with(
        "SELECT order_id, symbol, side, price, quantity, rsi, timestamp FROM orders WHERE DATE(timestamp) = :date ORDER BY timestamp DESC",
        {"date": "2026-06-10"}
    )
    
    # 3. Test get trades with invalid date format
    response = client.get("/api/v1/dashboard/trades?date=invalid-date")
    assert response.status_code == 400
    assert "Formato de fecha inválido" in response.json()["detail"]
    
    app.dependency_overrides.clear()
