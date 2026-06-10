## Why

El sistema actual usa reglas fijas (RSI, MACD, etc.) para generar señales, lo cual no se adapta a las condiciones cambiantes del mercado. Un modelo de Machine Learning puede aprender patrones más complejos y adaptarse a diferentes regímenes de mercado, mejorando la precisión de las señales.

## What Changes

- **Feature Engineering**: Extracción de features técnicos (RSI, MACD, Bollinger, ATR, volumen, etc.) para entrenamiento.
- **Modelo de Clasificación**: Clasificador binario (BUY/SELL/HOLD) basado en Random Forest o Logistic Regression.
- **Entrenamiento**: Pipeline de entrenamiento con datos históricos de Binance.
- **Predicción en Tiempo Real**: Integration del modelo entrenado para predicción de señales.
- **Ensemble**: Combinarpredicciones del modelo ML con estrategias existentes para mejorarlas.
- **Fallback**: Si modelo falla, usar estrategia tradicional como backup.

## Capabilities

### New Capabilities

- **ml-feature-engineering**: Generación de features técnicos para ML.
- **ml-training-pipeline**: Pipeline de entrenamiento del modelo.
- **ml-prediction**: Predicción en tiempo real con modelo entrenado.
- **ml-ensemble**: Combinación de ML con estrategias tradicionales.

## Impact

- **Nuevo Código**:
  - `app/services/ml/` - Módulo de ML
  - `app/services/ml/feature_engineering.py` - Feature extraction
  - `app/services/ml/model.py` - Modelo entrenable
  - `app/services/ml/predictor.py` - Predicción en tiempo real
- **Dependencias**: scikit-learn (solo para entrenamiento)
- **Configuración**: Parámetros de modelo, fecha de entrenamiento