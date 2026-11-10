import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.market_scanner import MarketScanner, EXCLUDED_BASE_ASSETS


def test_calculate_momentum_score():
    scanner = MarketScanner()

    # Base case: 5% gain, $25M volume (50% of benchmark)
    score_mid = scanner.calculate_momentum_score(price_change_pct=5.0, quote_volume=25_000_000.0)
    # 5.0 * 0.6 + 0.5 * 40.0 = 3.0 + 20.0 = 23.0
    assert score_mid == 23.0

    # High volume capped at $50M
    score_capped1 = scanner.calculate_momentum_score(price_change_pct=10.0, quote_volume=50_000_000.0)
    score_capped2 = scanner.calculate_momentum_score(price_change_pct=10.0, quote_volume=100_000_000.0)
    # Both should cap volume factor at 1.0 -> 10.0 * 0.6 + 40.0 = 46.0
    assert score_capped1 == 46.0
    assert score_capped2 == 46.0

    # Negative volume handled gracefully
    score_zero = scanner.calculate_momentum_score(price_change_pct=0.0, quote_volume=-100.0)
    assert score_zero == 0.0


@pytest.mark.anyio
async def test_scan_hot_markets_filtering():
    mock_client = MagicMock()
    mock_tickers = [
        # Excluded stablecoins
        {"symbol": "USDTUSDC", "quoteVolume": "50000000.0", "priceChangePercent": "0.1", "lastPrice": "1.0", "count": 100},
        {"symbol": "EURUSDC", "quoteVolume": "20000000.0", "priceChangePercent": "1.2", "lastPrice": "1.08", "count": 100},
        {"symbol": "FDUSDUSDC", "quoteVolume": "80000000.0", "priceChangePercent": "0.05", "lastPrice": "1.0", "count": 100},
        
        # Excluded Core symbols
        {"symbol": "BTCUSDC", "quoteVolume": "200000000.0", "priceChangePercent": "8.0", "lastPrice": "90000.0", "count": 5000},
        {"symbol": "ETHUSDC", "quoteVolume": "100000000.0", "priceChangePercent": "7.0", "lastPrice": "3200.0", "count": 3000},

        # Low volume (< $10M)
        {"symbol": "LOWVOLUSDC", "quoteVolume": "2000000.0", "priceChangePercent": "15.0", "lastPrice": "0.5", "count": 50},

        # Negative momentum
        {"symbol": "DUMPUSDC", "quoteVolume": "30000000.0", "priceChangePercent": "-4.5", "lastPrice": "12.0", "count": 800},

        # Hot candidates
        {"symbol": "DOGEUSDC", "quoteVolume": "45000000.0", "priceChangePercent": "12.0", "lastPrice": "0.38", "count": 4000},
        {"symbol": "NEARUSDC", "quoteVolume": "35000000.0", "priceChangePercent": "9.5", "lastPrice": "5.60", "count": 2500},
        {"symbol": "AVAXUSDC", "quoteVolume": "25000000.0", "priceChangePercent": "6.0", "lastPrice": "34.5", "count": 1800},
        {"symbol": "SUIUSDC", "quoteVolume": "15000000.0", "priceChangePercent": "4.0", "lastPrice": "3.10", "count": 1200},
    ]
    mock_client.get_tickers = AsyncMock(return_value=mock_tickers)

    scanner = MarketScanner(client=mock_client)
    candidates = await scanner.scan_hot_markets(
        quote_asset="USDC",
        top_n=3,
        min_volume=10_000_000.0,
        window_size="1h"
    )

    symbols = [c["symbol"] for c in candidates]
    # Top 3 should be DOGE, NEAR, AVAX
    assert len(candidates) == 3
    assert symbols == ["DOGEUSDC", "NEARUSDC", "AVAXUSDC"]

    # Verify no stablecoin or core symbol slipped in
    for c in candidates:
        assert c["base_asset"] not in EXCLUDED_BASE_ASSETS
        assert c["symbol"] not in {"BTCUSDC", "ETHUSDC", "USDTUSDC", "EURUSDC"}
        assert c["quote_volume"] >= 10_000_000.0
        assert c["price_change_pct"] > 0.0


def test_position_locking_filter_rotation_symbols():
    scanner = MarketScanner()

    current_symbols = ["DOGEUSDC", "NEARUSDC", "LINKUSDC"]
    # NEARUSDC has an active trade open
    locked_symbols = ["NEARUSDC"]

    scanned_candidates = [
        {"symbol": "AVAXUSDC", "score": 42.0},
        {"symbol": "SUIUSDC", "score": 38.0},
        {"symbol": "APTUSDC", "score": 35.0},
    ]

    plan = scanner.filter_rotation_symbols(
        current_symbols=current_symbols,
        scanned_candidates=scanned_candidates,
        locked_symbols=locked_symbols,
        max_symbols=3,
    )

    # NEARUSDC MUST be preserved
    assert "NEARUSDC" in plan["target_symbols"]
    assert "NEARUSDC" not in plan["to_remove"]
    assert "NEARUSDC" in plan["to_keep"]

    # Slots available: 3 total - 1 locked = 2 new slots for AVAX and SUI
    assert "AVAXUSDC" in plan["target_symbols"]
    assert "SUIUSDC" in plan["target_symbols"]
    assert "APTUSDC" not in plan["target_symbols"]

    # Additions & Removals
    assert set(plan["to_add"]) == {"AVAXUSDC", "SUIUSDC"}
    assert set(plan["to_remove"]) == {"DOGEUSDC", "LINKUSDC"}
    assert len(plan["target_symbols"]) == 3


def test_position_locking_all_locked():
    scanner = MarketScanner()

    current_symbols = ["DOGEUSDC", "NEARUSDC", "LINKUSDC"]
    # All 3 have open trades
    locked_symbols = ["DOGEUSDC", "NEARUSDC", "LINKUSDC"]

    scanned_candidates = [
        {"symbol": "AVAXUSDC", "score": 99.0},
        {"symbol": "SUIUSDC", "score": 88.0},
    ]

    plan = scanner.filter_rotation_symbols(
        current_symbols=current_symbols,
        scanned_candidates=scanned_candidates,
        locked_symbols=locked_symbols,
        max_symbols=3,
    )

    # NONE can be removed
    assert len(plan["to_remove"]) == 0
    assert len(plan["to_add"]) == 0
    assert set(plan["target_symbols"]) == set(current_symbols)
    assert set(plan["to_keep"]) == set(current_symbols)
