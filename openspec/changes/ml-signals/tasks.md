# ML Signals - Tasks

## Configuración

- [ ] 1.1 Añadir ML_ENABLED (bool, default: False) en app/core/config.py
- [ ] 1.2 Añadir ML_MODEL_PATH (str, default: "data/ml_models") en app/core/config.py
- [ ] 1.3 Añadir ML_CONFIDENCE_THRESHOLD (float, default: 0.5) en app/core/config.py

## Feature Engineering

- [ ] 2.1 Crear app/services/ml/feature_engineering.py
- [ ] 2.2 Implementar extract_features(klines) -> DataFrame
- [ ] 2.3 Implementar cálculo de 20 features (RSI, EMA, MACD, BB, ATR, Volume, Returns)
- [ ] 2.4 Implementar generate_labels(klines, threshold, horizon)
- [ ] 2.5 Implementar prepare_dataset(symbol, start, end) -> (X, y)

## Training Pipeline

- [ ] 3.1 Crear app/services/ml/trainer.py
- [ ] 3.2 Implementar RandomForestClassifier con default params
- [ ] 3.3 Implementar train(symbol, data) con cross-validation
- [ ] 3.4 Implementar save_model(model, path)
- [ ] 3.5 Implementar load_model(path)
- [ ] 3.6 Implementar evaluate(model, X_test, y_test) -> metrics

## Prediction

- [ ] 4.1 Crear app/services/ml/predictor.py
- [ ] 4.2 Implementar MLPredictor con load_model()
- [ ] 4.3 Implementar predict(symbol, features) -> signal
- [ ] 4.4 Implementar predict_with_proba(symbol, features) -> (signal, confidence)
- [ ] 4.5 Implementar caching de predicciones por candle

## Ensemble Integration

- [ ] 5.1 Crear app/services/ml/ensemble.py
- [ ] 5.2 Implementar combine_predictions(ml_signal, strategy_signal, ml_confidence)
- [ ] 5.3 Integrar en strategy_factory.py como filtro adicional
- [ ] 5.4 Implementar position multiplier según confianza

## CLI Commands

- [ ] 6.1 Crear comando: vinbot ml train --symbol BTCUSDT --days 180
- [ ] 6.2 Crear comando: vinbot ml predict --symbol BTCUSDT
- [ ] 6.3 Crear comando: vinbot ml status

## Testing

- [ ] 7.1 Tests unitarios para feature engineering
- [ ] 7.2 Tests de entrenamiento con datos mock
- [ ] 7.3 Tests de predicción
- [ ] 7.4 Tests de ensemble

## Documentación

- [ ] 8.1 Documentar cómo entrenar modelo
- [ ] 8.2 Documentar configuración de ML
- [ ] 8.3 Documentar interpretación de confianza