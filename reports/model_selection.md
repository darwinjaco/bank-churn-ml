# Selección de modelo — Semana 4

Generado con `uv run python -m churn.selection_report` desde [tuning.json](tuning.json) y [model_selection.json](model_selection.json) (spec 002 v1.4). Tres decimales; media ± desviación estándar muestral (ddof=1).

## Protocolo

FASE A: `RandomizedSearchCV` (20/40/40 iteraciones), 5 pliegues, semilla 42, AP. FASE B: mejores configuraciones en `RepeatedStratifiedKFold` 5x2, semilla 2027, idénticos para todas las familias. Entrenamiento: 6,000 filas. La prueba no se usa.

## FASE B

| Familia | AP búsqueda (optimista) | AP FASE B | ROC-AUC | Brier | Log loss |
|---|---|---|---|---|---|
| LogReg (FS-EDA) | 0.657 | 0.655 ± 0.027 | 0.839 ± 0.010 | 0.111 ± 0.004 | 0.364 ± 0.011 |
| Random Forest (FS-TREE) | 0.693 | 0.686 ± 0.018 | 0.854 ± 0.012 | 0.106 ± 0.003 | 0.350 ± 0.008 |
| XGBoost (FS-TREE) | 0.699 | 0.697 ± 0.018 | 0.860 ± 0.010 | 0.106 ± 0.003 | 0.349 ± 0.007 |

Diferencias pareadas frente al mejor (informativas):

- LogReg (FS-EDA) - XGBoost (FS-TREE): -0.042 ± 0.013 (0/10 pliegues positivos, 10/10 negativos)
- Random Forest (FS-TREE) - XGBoost (FS-TREE): -0.011 ± 0.009 (0/10 pliegues positivos, 10/10 negativos)

## Regla de selección (§6), paso a paso

1. **Mejor AP media de FASE B:** XGBoost (FS-TREE), 0.697 (std 0.018).
2. **Cercanos** (diferencia < std del mejor o media igual): Random Forest (FS-TREE), XGBoost (FS-TREE). Diferencias: LogReg (FS-EDA) 0.042; Random Forest (FS-TREE) 0.011; XGBoost (FS-TREE) 0.000. Por parsimonia se elige **Random Forest (FS-TREE)**.
3-5. **Validación** (primer uso; ajuste con las 6,000 filas de entrenamiento, AP en 2,000 filas):

| Modelo | AP validación |
|---|---|
| Dummy (FS-RAW) | 0.203 |
| Random Forest (FS-TREE) | 0.696 |
| LogReg (FS-EDA) | 0.637 |

Resultado del paso 4: `complejo_supera_logreg`. rf supera a Dummy y a LogReg en validación.

**Modelo final de la semana 4: Random Forest (FS-TREE)**, sin EstimatedSalary.

## Experimentos

### E-03: salario

Δ AP (sin - con `EstimatedSalary`): +0.003 ± 0.004 (8/10 pliegues positivos, 2/10 negativos). Umbral preregistrado: Δ ≥ -0.005 → eliminar. Decisión: se **elimina** `EstimatedSalary`.

### E-02: dependencia de `NumOfProducts` (auditoría, no elimina la variable)

- (a) Δ AP (sin - con `NumOfProducts`, configuración final): -0.113 ± 0.021 (0/10 pliegues positivos, 10/10 negativos).
- (b) AP por repetición, todos los clientes (n = 6,000): 0.688 / 0.686, media 0.687. Sin el grupo de 3-4 productos (n = 5,799): 0.609 / 0.607, media 0.608.
- (c) Grupo de 3-4 productos (n = 201): tasa observada 87.1%; probabilidad media predicha 73.2% (por repetición: 73.3% / 73.1%).

## Lectura descriptiva

- La diferencia entre XGBoost (FS-TREE) y el elegido es menor que la desviación del mejor; la regla prefiere el modelo más simple entre los cercanos.
- La re-evaluación en pliegues nuevos (FASE B) da AP ligeramente menores que la búsqueda, como se esperaba del sesgo optimista; el orden de las familias se mantiene.
- E-02 (b): el 3.4% de clientes con 3-4 productos aporta 0.079 de AP. La AP sin ese grupo es la referencia más honesta del rendimiento sobre el resto.
- E-02 (c): en ese grupo la probabilidad media predicha queda 13.9% por debajo de la tasa observada. Es un insumo para la calibración (E-04, semana 5) y la ficha del modelo (semana 6).
- Todas las métricas son de desarrollo: la validación se usó para elegir; la estimación independiente corresponde a la evaluación final en prueba.

## Hiperparámetros del modelo elegido

`n_estimators=500`, `random_state=42`, `n_jobs=-1`, `min_samples_leaf=5`, `max_features=sqrt`, `max_depth=10`

## Trazabilidad

Código de FASE A/B: `365185edb475ee92fe7d19f7db685a37ab2b7116`; selección y experimentos: `e0b5c7b3909e0e2ae6cc04ad8991d271f51c7139`. CSV SHA-256: `3996cd1fa372e0db0cd9c0ebac35bbd4e8e3c65fb942bb010c826e7b1eeef0a0`. Manifiesto SHA-256: `4354b7e0e711083f203540205cd8543f6cff9f767f2f05675fda9cf6e28ba8cc`. MLflow: `sqlite:///mlruns/mlflow.db`, experimento `bank-churn`.

| Corrida | Run ID |
|---|---|
| logreg-tuning | `7c2a2139a457449b91051527a7ef6a6e` |
| logreg-reevaluation | `eeb8d5fe97834720968e505890623dc4` |
| rf-tuning | `862e713ad9424cb68499c1d1d5346296` |
| rf-reevaluation | `569e1185bf344d3cb32f7289bc35ebb0` |
| xgb-tuning | `e5cd9a4fe70a4de9bd9a84bd2c986bc0` |
| xgb-reevaluation | `caab087c67274591b0eed37c92210b82` |
| e03 | `127b0f74d20f4ff8ba294ae6c150ae51` |
| e02 | `39a39e18dbca48c9b5e881edfa3bd3bd` |
| selection | `563a493143ff4f788042393f361e39cd` |
