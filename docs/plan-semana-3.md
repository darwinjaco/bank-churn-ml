# SEMANA 3 (19–25 oct) — Pipeline, baselines y MLflow

Rol: implementador. Las reglas de `AGENTS.md` siguen vigentes (compuerta SDD, no cargar test, Gender nunca como feature).

Presupuesto: ~7,5 h. Una tarea = un commit. Comprobaciones de `AGENTS.md` en verde antes de cada commit.

## T0 — COMPUERTA (solo documentación) · 1 h

1. Crea `docs/plan-semana-3.md` con este texto completo (T0–T7).
2. Enmienda la spec 002 a v1.1. Cabecera: «v1.1 — incorpora los hallazgos de la semana 2 (spec 003)».

   §3, sustituye la tabla de preprocesamiento por dos conjuntos de variables:

   | Conjunto | Uso | Definición |
   |---|---|---|
   | FS-RAW | Referencia ingenua | CreditScore, Age, Tenure, Balance, EstimatedSalary, NumOfProducts (entero), HasCrCard, IsActiveMember, Geography (one-hot, `handle_unknown="error"`). Numéricas con `StandardScaler` en modelos lineales |
   | FS-EDA | LogReg informada por H1–H6 | FS-RAW con estos cambios: NumOfProducts → one-hot de {1, 2, 3–4} (H2: no monótona; mapeo sin estado `clip(upper=3)`); Age → `StandardScaler` + término cuadrático, ajustados dentro de cada pliegue (H4); se añade `has_balance` (H5, Q-10); Balance continuo escalado; EstimatedSalary se mantiene hasta E-03 |

   §3, nuevas reglas:
   - R1. Toda transformación con parámetros aprendidos de los datos (medias, escalas, categorías) es un transformador sklearn dentro del Pipeline. Prohibido calcular estadísticos fuera del pipeline. `config.centered_age()` queda solo para la inferencia de la spec 003, nunca en modelado.
   - R2. Las transformaciones sin estado (`has_balance`, clip de NumOfProducts) usan constantes fijas.
   - R3. Sin remuestreo (SMOTE, undersampling) ni `class_weight`: las probabilidades deben conservar la escala real para la calibración y la decisión económica (specs 002 §5.3 y 004).
   - R4. Q-10: `has_balance` y `Geography` comparten señal. Sus coeficientes LogReg no se interpretan por separado; en la semana 6, SHAP se reporta agrupando ambas.
   - R5. `age_band` deja de ser candidata en modelos lineales; la sustituye el término cuadrático (H4). Los árboles (semana 4) usan Age sin transformar.

   §5.1, añade:
   - La semana 3 evalúa SOLO con validación cruzada estratificada de 5 pliegues sobre entrenamiento (6.000 filas; `shuffle=True`; seed 42; mismos pliegues para todos los modelos). La validación no se usa en la semana 3.
   - Métricas por pliegue: AP (principal), ROC-AUC, Brier y log loss. Reporte: media ± desviación estándar muestral (`ddof=1`).

   §5.4 (nueva), trazabilidad en MLflow:
   - Tracking URI desde la variable `MLFLOW_TRACKING_URI`; por defecto `sqlite:///mlruns/mlflow.db` (`mlruns/` fuera de Git). Experimento: `bank-churn`.
   - Parámetros: modelo, conjunto de variables, hiperparámetros, `n_folds`, seed.
   - Métricas: media y desviación de cada métrica, más las métricas por pliegue con step = número de pliegue.
   - Etiquetas: `stage=baseline`, `git_commit`, `csv_sha256`, `split_manifest_sha256`, `eligible` (false para Dummy), `final=false`.

   §4, configuración fija de la semana 3 (sin ajuste de hiperparámetros):
   - Dummy: `DummyClassifier(strategy="prior")` con FS-RAW.
   - LogReg: penalty L2, `C=1.0`, solver lbfgs, `max_iter=1000`, con FS-RAW y con FS-EDA.
   - En total, 3 corridas: `dummy-raw`, `logreg-raw`, `logreg-eda`.

3. Registro: renumera si hace falta, abre S07 con fecha y objetivo, y anota la enmienda v1.1 con su motivo.

Commit: `docs: amend spec 002 v1.1 and week 3 plan (SDD gate)`.

## T1 — DEUDA DE LA SEMANA 2: FIGURAS · 30 min

`src/churn/plots.py`, solo presentación (no cambia datos ni cálculos):
- Formateador de miles («50k») en los ejes X de salary_distribution y balance_distribution.
- `constrained_layout=True` en todas las figuras con varios paneles.
- Un único color para todas las barras y puntos.
- germany_or: línea vertical discontinua en OR = 1,5 con etiqueta «umbral práctico» y menos espacio vertical.
- Títulos con ID: H1 actividad, H2 productos, H3 Alemania, H4 edad, H5 saldo, H6 salario.
- Tasas en % (`PercentFormatter`).

Regenera las 6 PNG (cada una <200 KB) y comprueba visualmente que no haya solapamientos.

Commit: `fix: figure readability (week 2 debt)`.

## T2 — DEPENDENCIAS · 15 min

- Añade `mlflow` (si el tamaño rompe el CI, propón `mlflow-skinny` y regístralo como bloqueo; no decidas tú).
- `uv lock`; `uv sync --locked --all-groups`. Los tests usan un tracking URI temporal (`tmp_path`) y nunca escriben en `mlruns/`.

Commit: `build: add mlflow`.

## T3 — VARIABLES (`src/churn/features.py`) · 1 h

- Transformadores sklearn (`BaseEstimator`, `TransformerMixin`), con `get_feature_names_out`:
  - `HasBalance`: sin estado, Balance > 0 → 0/1.
  - `ProductsGroup`: sin estado, `NumOfProducts.clip(upper=3)` → categorías {1, 2, 3} (3 = «3–4»).
  - Edad cuadrática: `StandardScaler` seguido de `PolynomialFeatures(degree=2, include_bias=False)`, solo sobre Age.
- `FEATURE_SETS` en `config.py`: `{"raw": [...], "eda": [...]}` con las columnas de entrada de cada conjunto.

Tests (`tests/test_features.py`):
- Ningún conjunto incluye Gender, RowNumber, CustomerId ni Surname.
- HasBalance y ProductsGroup son deterministas y no tienen estado (fit no cambia nada).
- El escalado de edad aprende la media del conjunto de ajuste: si se ajusta con A y se transforma B, la media usada es la de A (test de no fuga).

Commit: `feat: leakage-safe feature transformers`.

## T4 — PIPELINE (`src/churn/pipeline.py`) · 1 h 15 min

- `build_pipeline(model: str, feature_set: str) -> sklearn.Pipeline` (ColumnTransformer + modelo), con model ∈ {dummy, logreg} y feature_set ∈ {raw, eda}. Configuraciones según la spec 002 §4 v1.1.
- Si el DataFrame de entrada contiene Gender, levanta `ValueError` (defensa explícita de D-02, no se ignora en silencio).
- `OneHotEncoder(handle_unknown="error")`.

Tests (`tests/test_pipeline.py`):
- Ajusta y predice en datos sintéticos; las probabilidades están en [0, 1].
- Un DataFrame con Gender produce `ValueError`.
- Una categoría de Geography desconocida produce error.
- Los nombres de salida no contienen Gender ni IDs.

Commit: `feat: model pipelines for baselines`.

## T5 — VALIDACIÓN CRUZADA Y MLFLOW (`src/churn/train.py`) · 2 h

- `load_training()`: filtra `load_exploration()` a `partition == "train"`. NO existe un loader de test ni de validación para entrenar.
- `cross_validate_model(pipeline, X, y)` → métricas por pliegue y resumen. `StratifiedKFold(5, shuffle=True, random_state=42)`.
- `log_run(...)` a MLflow según la spec 002 §5.4.
- CLI `churn-baselines`: ejecuta las 3 corridas y escribe `reports/baselines.json` (por pliegue + resumen).

Tests (`tests/test_train.py`):
- Dummy en datos sintéticos: ROC-AUC = 0,5 y AP ≈ prevalencia (±0,02).
- Determinismo: dos ejecuciones dan métricas idénticas.
- Los pliegues son idénticos entre modelos.
- `load_training()` no contiene ningún CustomerId de validación ni de test.
- MLflow: la corrida registra los parámetros, métricas y etiquetas obligatorios (tracking URI temporal).

Commit: `feat: cross-validation harness with MLflow tracking`.

## T6 — EJECUCIÓN REAL · 45 min

- `uv run churn-baselines` (con el CSV local).
- `reports/baselines.md` generado desde `baselines.json`: tabla modelo × {AP, ROC-AUC, Brier, log loss} con media ± std.
- Sin conclusiones de selección: la selección es de la semana 4 (spec 002 §6).

Commit: `chore: baseline results`.

## T7 — CIERRE · 45 min

- `reports/baselines.md`: 3–5 líneas de lectura descriptiva (¿logreg-eda mejora a logreg-raw en AP más que la desviación estándar?), sin elegir modelo ni usar lenguaje causal.
- README: tabla de baselines y hoja de ruta.
- Registro: cierra S07 con comandos, resultados, URL del CI y ubicación de las corridas en MLflow (local).

Commit: `docs: week 3 results and log`.

**Al terminar T7: detenerse y esperar la revisión. Si algún punto no está en la spec 002 v1.1: detenerse y registrarlo como bloqueo.**
