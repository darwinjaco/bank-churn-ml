# Calibración y decisión — Semana 5

Generado con `uv run python -m churn.decision_report` desde [decision.json](decision.json) (spec 002 v1.5 §5.3.1 y spec 004 v1.0, opción A). Todas las cifras son de validación (2.000 clientes) y de **desarrollo**: la validación ya se usó para elegir modelo y calibrador. La prueba sigue sin usarse.

## E-04: calibración

Calibradores ajustados con predicciones OOF de las 6.000 filas de entrenamiento (5 pliegues, semilla 42) y comparados en validación por Brier; empate si la diferencia es < 1e-4.

| Variante | Brier | Log loss | AP | Predicho grupo 3-4 |
|---|---|---|---|---|
| Sin calibrar | 0.1026 | 0.3409 | 0.696 | 73.4% |
| Sigmoide (elegida) | 0.1010 | 0.3361 | 0.696 | 84.1% |
| Isotónica | 0.1013 | 0.3540 | 0.673 | 83.6% |

Grupo de 3-4 productos en validación: n = 56, tasa observada 80.4%. Figura: [reliability.png](figures/reliability.png).

## Regla de decisión (opción A)

Supuestos ilustrativos: V = 1.000 €, c = 50 €, s = 30%. Contactar si p > t\* = c / (s·V) = 0.1667. El umbral es analítico: no se ajustó con datos.

## Beneficio en validación

2.000 clientes, 407 abandonos. Beneficio = suma sobre contactados de (y·s·V - c).

| Política | Contactados | Abandonos captados | Beneficio |
|---|---|---|---|
| Nadie | 0 | 0 | 0 € |
| Todos | 2.000 | 407 | 22.100 € |
| Aleatoria 20 % (valor esperado) | 400 | 81 | 4.420 € |
| **Modelo (p calibrada > t\*)** | 621 | 310 | 61.950 € |
| Oráculo (cota superior) | 407 | 407 | 101.750 € |

- Mejor referencia sin modelo: **Todos**; el modelo aporta 39.850 € más.

- El modelo captura el 60.9% del beneficio del oráculo contactando al 31.1% de los clientes.

- En t\*: precisión 0.499, sensibilidad 0.762, F1 0.603. Matriz de confusión: VN 1282, FP 311, FN 97, VP 310.

## Límites (spec 004 §4)

- Los supuestos económicos son ilustrativos; con otros valores cambian t\* y el beneficio. Deciles y sensibilidad quedaron fuera del alcance por decisión del responsable.
- La campaña se supone efectiva solo en quienes iban a irse, con la misma tasa s para todos y sin efectos negativos; no hay datos de tratamiento para estimar *uplift*.
- V es igual para todos: el dataset no tiene ingresos por cliente.
- Cifras de desarrollo; la estimación independiente corresponde a la evaluación final en prueba.

## Trazabilidad

Commit: `f2796d55bd2bd4683b6745516061486654b43bba`. CSV SHA-256: `3996cd1fa372e0db0cd9c0ebac35bbd4e8e3c65fb942bb010c826e7b1eeef0a0`. Manifiesto (canónico): `09ee6a9697dc06695524f3fea4b34b2bacf34943592c21603e11340eb5c73397`. MLflow: calibración `0ba473f6e4594a74bea026e68bb0a71c`, decisión `ae0f524498724988be456d8cf1082e49`. Artefacto en `models/` (fuera de Git); metadata en [model_metadata.json](model_metadata.json).
