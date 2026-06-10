## Context

El objetivo es añadir capacidades de Machine Learning al sistema de trading sinincrementar complejidad operativa. El modelo debe ser ligero, rápido de entrenar, y capaz de correr en producción.

## Goals / Non-Goals

**Goals:**
- Crear sistema de features técnicos para ML
- Entrenar modelo clasificador simple (Random Forest o Logistic Regression)
- Integrarpredicciones del modelo como filtro adicional
- Combinar con estrategias existentes (ensemble)

**Non-Goals:**
- No se usará deep learning (LSTM, Transformer) - muy pesado
- No se entrenará en tiempo real - solo offline
- No se usará AutoML complejo
- No se creará modelo de predicción de precio, solo dirección

## Decisions

### D1: Modelo

**Decisión**: Usar Random Forest Classifier por su robustez y capacidad de manejar features complejos.

**Alternativas**: Logistic Regression (más simple pero menos preciso), XGBoost (más preciso pero más complejo)

**Rationale**: Random Forest ofrece buen balance entre accuracy y speed, no requiere GPU, y es interpretable.

### D2: Features

**Decisión**: Usar 20 features técnicos básicos:
- RSI (3 períodos: 7, 14, 21)
- EMA (3 períodos: 9, 21, 50)
- MACD (line, signal, histogram)
- Bollinger Bands (position)
- ATR (normalized)
- Volume (actual vs average)
- Returns (1d, 3d, 7d)

**Rationale**: Features que se calculan rápido y son relevantes para el trading.

### D3: Labels

**Decisión**: Labels basados en returns futuros:
- BUY: price goes up > X% in next N candles
- SELL: price goes down > X% in next N candles
- HOLD: otherwise

**Rationale**: Clasificación directa basada en resultado, más simple que secuencia.

### D4: Ensemble

**Decisión**: El modelo ML se usa como filtro:
- Si ML dice BUY Y estrategia tradicional dice BUY → BUY (alta confianza)
- Si ML dice BUY pero estrategia dice HOLD → CHECK (revisar manualmente)
- Si ML dice HOLD → seguir estrategia tradicional

**Rationale**: El modelo mejora la señal pero no la reemplaza completamente.

### D5: Retraining

**Decisión**: Retrain mensual con datos de los últimos 6 meses.

**Rationale**: Mantiene el modelo actualizado sin sobreentrenar.

## Risks / Trade-offs

### R1: Overfitting

**Riesgo**: El modelo puede memorize patrones históricos que no se repiten.

**Mitigación**: Cross-validation, limited tree depth, regularization.

### R2: Feature Drift

**Riesgo**: Distribuciones de features cambian con el tiempo.

**Mitigación**: Retraining periódico, monitoring de feature distributions.

### R3: Latency

**Riesgo**: Predicción Adds latency al sistema.

**Mitigación**: Cache predictions, async prediction, simple model.

## Migration Plan

1. **Fase 1**: Feature engineering module
2. **Fase 2**: Training pipeline con datos históricos
3. **Fase 3**: Modelo entrenado serializado (joblib/pickle)
4. **Fase 4**: Predictor en tiempo real
5. **Fase 5**: Ensemble con estrategias existentes