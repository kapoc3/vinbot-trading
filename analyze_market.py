#!/usr/bin/env python3
"""
Backtest Analyzer - Analiza datos históricos para encontrar patrones rentables
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from app.services.indicators import get_symbol_data, market_indicators
from app.services.binance_client import ProductionBinanceClient
from app.core.config import get_settings

async def analyze_symbol(symbol: str, klines: list) -> dict:
    """Analizar un símbolo y encontrar mejores puntos de entrada/salida"""
    # Cargar datos en el indicador
    symbol_data = get_symbol_data(symbol)
    symbol_data.closes = [float(k[4]) for k in klines]  # closing prices
    symbol_data.highs = [float(k[2]) for k in klines]
    symbol_data.lows = [float(k[3]) for k in klines]
    symbol_data.volumes = [float(k[5]) for k in klines]
    
    # Calcular RSI para diferentes períodos
    results = {}
    for period in [7, 14, 21]:
        rsi = symbol_data.get_rsi(period)
        results[f'rsi_{period}'] = rsi
    
    # Encontrar oversold/overbought históricos
    oversold_count = sum(1 for r in [results.get('rsi_7'), results.get('rsi_14'), results.get('rsi_21')] if r and r < 35)
    overbought_count = sum(1 for r in [results.get('rsi_7'), results.get('rsi_14'), results.get('rsi_21')] if r and r > 65)
    
    # Calcular momentum
    if len(symbol_data.closes) > 14:
        current_price = symbol_data.closes[-1]
        avg_price = sum(symbol_data.closes[-14:]) / 14
        momentum = ((current_price - avg_price) / avg_price) * 100
    else:
        momentum = 0
    
    return {
        'symbol': symbol,
        'current_price': symbol_data.closes[-1] if symbol_data.closes else 0,
        'rsi_7': results.get('rsi_7'),
        'rsi_14': results.get('rsi_14'),
        'rsi_21': results.get('rsi_21'),
        'oversold_count': oversold_count,
        'overbought_count': overbought_count,
        'momentum': momentum,
        'volatility': (max(symbol_data.closes[-20:]) - min(symbol_data.closes[-20:])) / min(symbol_data.closes[-20:]) * 100 if len(symbol_data.closes) >= 20 else 0
    }

async def main():
    client = ProductionBinanceClient()
    await client.sync_time()
    
    settings = get_settings()
    symbols = settings.TRADING_SYMBOLS.split(',')
    
    print("=" * 60)
    print("ANÁLISIS DE MERCADO PARA TRADING")
    print("=" * 60)
    
    recommendations = []
    
    for symbol in symbols:
        symbol = symbol.strip()
        if not symbol:
            continue
            
        # Obtener últimos 200 klines (aprox 3+ horas de datos)
        import httpx
        try:
            resp = await client.client.get("/api/v3/klines", params={
                'symbol': symbol,
                'interval': '1m',
                'limit': 200
            })
            klines = resp.json()
            
            analysis = await analyze_symbol(symbol, klines)
            
            print(f"\n{analysis['symbol']}:")
            print(f"  Precio actual: ${analysis['current_price']:.4f}")
            print(f"  RSI-7:  {analysis['rsi_7']:.2f}" if analysis['rsi_7'] else "  RSI-7: N/A")
            print(f"  RSI-14: {analysis['rsi_14']:.2f}" if analysis['rsi_14'] else "  RSI-14: N/A")
            print(f"  RSI-21: {analysis['rsi_21']:.2f}" if analysis['rsi_21'] else "  RSI-21: N/A")
            print(f"  Momentum: {analysis['momentum']:.2f}%")
            print(f"  Volatilidad: {analysis['volatility']:.2f}%")
            
            # Determinar recomendación
            rsi = analysis['rsi_14'] or 50
            
            if rsi < 30:
                rec = "COMPRA FUERTE (RSI oversold)"
                score = 3
            elif rsi < 40:
                rec = "COMPRA (RSI bajo)"
                score = 2
            elif rsi > 70:
                rec = "VENTA (RSI overbought)"
                score = -1
            elif rsi > 60:
                rec = "VENTA PARCIAL (RSI alto)"
                score = -0.5
            else:
                rec = "ESPERAR (zona neutral)"
                score = 0
            
            print(f"  -> {rec}")
            
            recommendations.append({
                'symbol': symbol,
                'score': score,
                'rsi': rsi,
                'momentum': analysis['momentum'],
                'recommendation': rec
            })
            
        except Exception as e:
            print(f"\n{symbol}: Error - {e}")
    
    # Ordenar por mejor oportunidad
    print("\n" + "=" * 60)
    print("RANKING DE OPORTUNIDADES")
    print("=" * 60)
    
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    
    for i, rec in enumerate(recommendations, 1):
        emoji = "🟢" if rec['score'] > 0 else ("🔴" if rec['score'] < 0 else "⚪")
        print(f"{i}. {emoji} {rec['symbol']}: RSI={rec['rsi']:.1f}, Momentum={rec['momentum']:.1f}%")
        print(f"   {rec['recommendation']}")
    
    print("\n" + "=" * 60)
    print("RECOMENDACIÓN DE CONFIGURACIÓN")
    print("=" * 60)
    best_buy = next((r for r in recommendations if r['score'] > 0), None)
    if best_buy:
        print(f"Mejor símbolo para COMPRAR: {best_buy['symbol']}")
        print(f"  RSI actual: {best_buy['rsi']:.2f}")
        print(f"  Momentum: {best_buy['momentum']:.2f}%")
    else:
        print("No hay símbolos en zona de compra clara.")
        print("Esperando a que RSI baje de 35 para comprar.")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())