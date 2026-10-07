# Ficha del modelo — Abandono bancario → decisiones de retención

Generada con `uv run python -m churn.model_card` desde los JSON de `reports/`.

## Resumen

Random Forest calibrado (sigmoid) que estima la probabilidad de abandono de un cliente y recomienda contactarlo si el beneficio esperado de la campaña es positivo (p > 0.1667).

## Uso previsto y no previsto

- **Previsto:** priorizar contactos de retención en un ejercicio de portafolio con datos públicos; demostrar un flujo reproducible de modelado y decisión.
- **No previsto:** decisiones reales sobre clientes, crédito o precios; cualquier uso con datos de una institución sin revalidar, recalibrar y revisar supuestos; interpretaciones causales.

## Datos

Churn Modelling (Kaggle), 10.000 clientes, probablemente sintético. División estratificada 60/20/20 (semilla 42) con manifiesto versionado. Entrenamiento 6.000; validación 2.000 (usada para seleccionar y calibrar); prueba 2.000 reservada.

## Variables

- Entradas: CreditScore, Age, Tenure, Balance, NumOfProducts, HasCrCard, IsActiveMember, Geography (+ `has_balance` derivada).
- Excluidas: identificadores; `Gender` (solo auditoría, D-02); EstimatedSalary (E-03).

## Entrenamiento y selección

Búsqueda en dos fases (spec 002 §5.1) entre LogReg, Random Forest y XGBoost; regla de parsimonia de §6. Random Forest: AP en FASE B 0.686 ± 0.018; AP en validación 0.696. Hiperparámetros: n_estimators=500, random_state=42, n_jobs=-1, min_samples_leaf=5, max_features=sqrt, max_depth=10.

## Calibración y decisión

- Brier en validación: sin calibrar 0.1026, sigmoid 0.1010.
- Regla: contactar si p > c / (s·V) con V = 1.000 €, c = 50 €, s = 30% (supuestos ilustrativos).
- Validación: el modelo contacta a 621 de 2.000 clientes y obtiene 61.950 €, frente a 22.100 € contactando a todos; 60.9% del oráculo.

## Explicabilidad y equidad

- Variables más influyentes (SHAP): Age, NumOfProducts, IsActiveMember, Geography=Germany.
- E-01 (género): alertas preregistradas: Precisión. Tasa de contacto 31.2% frente a 31.0%; sensibilidad 77.5% frente a 74.7%. Detalle en [audit.md](audit.md).

## Limitaciones

- Datos probablemente sintéticos: los resultados no son evidencia bancaria real.
- El grupo de 3-4 productos (≈3 % de clientes) aporta una parte importante de la AP (E-02: AP 0.687 con todos frente a 0.608 sin ese grupo).
- Alemania no tiene clientes con saldo cero (Q-10): saldo y geografía comparten señal.
- Los abandonos de clientes jóvenes y activos son los más difíciles de detectar.
- Supuestos económicos ilustrativos e iguales para todos; sin datos de tratamiento (*uplift*); sin análisis de sensibilidad (fuera de alcance por decisión del responsable).
- Las métricas de validación son de desarrollo.

## Evaluación final en prueba

Única evaluación, el 2026-10-07, sobre 2.000 clientes nunca usados (abandono 20.3%), con modelo, calibrador y umbral congelados. Es la estimación independiente del rendimiento.

| Métrica | Prueba | Validación (desarrollo) |
|---|---|---|
| AP | 0.705 | 0.696 |
| ROC-AUC | 0.862 | — |
| Brier | 0.1017 | 0.1010 |
| Contactados | 634 | 621 |
| Beneficio del modelo | 61.600 € | 61.950 € |
| Beneficio contactando a todos | 22.100 € | 22.100 € |
| Fracción del oráculo | 60.5% | 60.9% |

En t*: precisión 0.491, sensibilidad 0.764. AP de FASE B (CV de entrenamiento): 0.686 ± 0.018.

## Trazabilidad

Artefacto: commit `f2796d55bd2bd4683b6745516061486654b43bba`; CSV `3996cd1fa372…`; manifiesto `09ee6a9697dc…`; versiones python 3.11.16, scikit-learn 1.9.1, xgboost 3.2.0, numpy 2.4.6, pandas 3.0.6.
