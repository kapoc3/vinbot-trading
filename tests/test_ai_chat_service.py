import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.ai_chat_service import AIChatService


def test_ai_chat_service_offline_handling():
    async def _run():
        service = AIChatService()

        with patch.object(service, "check_ollama_status", new_callable=AsyncMock) as mock_st:
            mock_st.return_value = {
                "online": False,
                "target_model": "qwen2.5:7b",
                "model_available": False,
                "installed_models": [],
                "message": "Offline"
            }

            res = await service.ask_analyst("¿Cómo van las ganancias?")
            assert res["status"] == "offline"
            assert "El motor de IA local no está accesible" in res["reply"]
            assert "ollama serve" in res["reply"]

    asyncio.run(_run())


def test_ai_chat_service_success():
    async def _run():
        service = AIChatService()

        mock_ollama_response = MagicMock()
        mock_ollama_response.status_code = 200
        mock_ollama_response.json.return_value = {
            "message": {"content": "Las ganancias de hoy son de +$2.40 USDC con 70% win rate."},
            "total_duration": 1500000000
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_ollama_response
        mock_client.is_closed = False

        with patch.object(service, "check_ollama_status", new_callable=AsyncMock) as mock_st, \
             patch.object(service, "_get_client", return_value=mock_client), \
             patch("app.services.ai_chat_service.db.execute") as mock_db:

            mock_st.return_value = {
                "online": True,
                "target_model": "qwen2.5:7b",
                "model_available": True,
                "installed_models": ["qwen2.5:7b"],
                "message": "Ready"
            }

            mock_cursor = AsyncMock()
            mock_cursor.fetchall.return_value = []
            mock_db.return_value = mock_cursor

            res = await service.ask_analyst("¿Cuánto ganamos hoy?")
            assert res["status"] == "success"
            assert "Las ganancias de hoy" in res["reply"]
            assert res["total_duration_ms"] == 1500.0

    asyncio.run(_run())


def test_ai_chat_service_context_summary():
    async def _run():
        service = AIChatService()
        summary = await service.build_trading_context_summary()
        assert "VINBOT REAL-TIME TRADING SNAPSHOT" in summary
        assert "PnL Neto Diario" in summary
        assert "Comisiones Totales Pagadas" in summary
        assert "Volumen Total Transaccionado" in summary

    asyncio.run(_run())
