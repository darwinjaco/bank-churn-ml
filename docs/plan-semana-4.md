# SEMANA 4 (26 oct – 1 nov) — RF, XGBoost, ajuste acotado, selección y ablaciones E-02/E-03

Rol: implementador. Las reglas de `AGENTS.md` siguen vigentes: compuerta SDD, no cargar test, Gender nunca como feature, una tarea = un commit y comprobaciones en verde antes de cada commit.

Presupuesto: ~8 h. Si algo no está en la spec 002 v1.2: detenerse y registrarlo como bloqueo.

## Observaciones pendientes de semana 3 (van en T0)

- **O1.** `reports/baselines.md`: mostrar métricas con tres decimales; con std ≈ 0,03, el resto es ruido.
- **O2.** Añadir la diferencia pareada por pliegue LogReg-EDA − LogReg-RAW (media ± std de las diferencias, ddof=1 y signo en cada pliegue). Valor esperado: AP +0,198 ± 0,019; 5/5 positivos. Calcular desde `baselines.json`, no a mano.
- **O3.** Cabecera Estado de la spec 002: «En implementación: semanas 3–4 completadas/en curso».

## T0 — COMPUERTA (solo documentación) · 1 h

1. Crear `docs/plan-semana-4.md` con este texto completo.
2. Aplicar O1–O3. O1/O2 se generan desde el JSON con el script de reportes existente; si requieren cambiar código de reportes, hacerlo en T1, no aquí.
3. Enmendar spec 002 a v1.2: «v1.2 — protocolo de la semana 4 fijado antes de entrenar».

   §3, conjunto para árboles:

   | Conjunto | Uso | Definición |
   |---|---|---|
   | FS-TREE | RF y XGBoost | CreditScore, Age, Tenure, Balance, EstimatedSalary, NumOfProducts (entero, sin agrupar: los árboles modelan la no monotonía), HasCrCard, IsActiveMember, Geography (one-hot) + has_balance. Sin escalado ni término cuadrático |

   - `balance_to_salary` deja de ser candidata (H6: salario sin señal univariada; E-03 decide sobre salario). `age_band` ya se había descartado (R5).
   - R3 también aplica a árboles: sin `class_weight`, `scale_pos_weight=1`, sin remuestreo.

   §5.1, protocolo en dos fases para reducir sesgo optimista del ajuste:
   - **FASE A:** `RandomizedSearchCV` de entrenamiento, `StratifiedKFold(5, shuffle=True, random_state=42)`, `scoring="average_precision"`, `refit=False`. Presupuesto LogReg 20, RF 40, XGBoost 40; búsqueda `random_state=42`.
   - **FASE B:** mejor configuración de cada familia reevaluada en pliegues nuevos, `RepeatedStratifiedKFold(n_splits=5, n_repeats=2, random_state=2027)`, iguales entre familias. La regla §6 usa AP medias de B, no de búsqueda.
   - Motivo: seleccionar el máximo entre configuraciones infla el puntaje de búsqueda, más en familias con más parámetros.
   - Reporte adicional informativo: diferencia pareada de AP por pliegue B entre cada familia y la mejor; no cambia la regla congelada de §6.

   §4, espacios de búsqueda (distribuciones de `scipy.stats`):
   - LogReg (FS-EDA): `C ~ loguniform(1e-3, 1e2)`; L2, lbfgs, `max_iter=2000`.
   - RF (FS-TREE): `n_estimators=500` fijo; `max_depth ∈ {None, 4, 6, 8, 10, 12, 16}`; `min_samples_leaf ∈ {1, 2, 5, 10, 20, 50}`; `max_features ∈ {"sqrt", 0.3, 0.5, 0.8}`; `random_state=42`; `n_jobs=-1`.
   - XGBoost (FS-TREE): `n_estimators ∈ {100, 200, 400, 800}`; `learning_rate ~ loguniform(0.01, 0.3)`; `max_depth ∈ {2, 3, 4, 5, 6}`; `min_child_weight ∈ {1, 3, 5, 10}`; `subsample ~ uniform(0.6, 0.4)`; `colsample_bytree ~ uniform(0.6, 0.4)`; `reg_lambda ~ loguniform(0.1, 10)`; `tree_method="hist"`; `scale_pos_weight=1`; `eval_metric="logloss"`; `random_state=42`; `n_jobs=-1`. Sin early stopping.

   §6, primera utilización de validación en modelado:
   - Solo para pasos 3–4 de la regla; cada candidato necesario se ajusta con todo entrenamiento y calcula AP de validación una vez. MLflow `stage=selection`.
   - Sin ajustar hiperparámetros ni variables con validación.

   §7, experimentos sobre familia seleccionada, hiperparámetros fijos sin reajuste, en pliegues B:
   - **E-03:** Δ = AP(sin EstimatedSalary) − AP(con), pareada. Si media(Δ) ≥ −0,005, eliminar salario por parsimonia; en caso contrario conservarlo.
   - **E-02:** auditoría, no decisión de eliminar productos (H2). Reportar (a) AP con/sin NumOfProducts pareada; (b) AP OOF de B excluyendo clientes con NumOfProducts ≥3 para rendimiento sin grupo fácil Q-03; (c) grupo 3–4, probabilidad media predicha frente a tasa observada, con n. Alimenta ficha de semana 6.

   §6, orden fijo:
   FASE A → FASE B → regla pasos 1–2 → E-03 (variables finales) → E-02 (auditoría) → ajuste con variables finales en entrenamiento → validación, pasos 3–4 (candidato y, si es complejo, LogReg con la misma decisión de variables).

4. Registro: abrir S08 y anotar la enmienda v1.2 con motivo.

Commit: `docs: amend spec 002 v1.2 and week 4 plan (SDD gate)`.

## T1 — REPORTES DE SEMANA 3 (si O1/O2 requieren código) · 20 min

- Funciones de reporte: tres decimales en tablas legibles y diferencia pareada por pliegue.
- Regenerar `reports/baselines.md`. Test: diferencia pareada desde JSON sintético.

Commit: `fix: baseline report precision and paired differences`.

## T2 — DEPENDENCIA · 10 min

- Añadir `xgboost`; `uv lock`; `uv sync --locked --all-groups`.

Commit: `build: add xgboost`.

## T3 — PIPELINES DE ÁRBOLES · 1 h

- `build_pipeline`: modelos {rf, xgb} con feature_set `tree` (FS-TREE), conservando InputGuard.
- Espacios como constantes en `src/churn/search_spaces.py`, copiados de §4 v1.2.

Tests:
- Espacios coinciden exactamente con spec: claves, valores y distribuciones.
- Árboles rechazan Gender, no escalan y producen probabilidades en [0,1].
- Sin `class_weight` ni `scale_pos_weight` diferentes de valores por defecto/1 (R3).
- Dos ajustes con misma semilla producen predicciones idénticas.

Commit: `feat: tree pipelines and preregistered search spaces`.

## T4 — AJUSTE Y REEVALUACIÓN (`src/churn/tune.py`) · 1 h 30 min

- `tune_family(family)`: FASE A con `load_training()`. MLflow `stage=tuning`, mejor configuración y puntaje de búsqueda marcado optimista.
- `reevaluate(configs)`: FASE B, pliegues repetidos semilla 2027; AP, ROC-AUC, Brier y log loss por pliegue; OOF en `data/processed/oof_phaseB.parquet`, fuera de Git.
- CLI `churn-tune` → `reports/tuning.json`.
- Tests sintéticos y presupuesto reducido: pliegues B idénticos entre familias y distintos de A; sin validación externa, solo `load_training()`.

Commit: `feat: two-phase tuning and re-evaluation`.

## T5 — REGLA DE SELECCIÓN (`src/churn/selection.py`) · 1 h

- `select_model(cv_summary, val_scores=None)` pura; implementa §6 pasos 1–5 tal como están escritos, sin reinterpretación.
- Tests, un caso por rama: claramente mejor; cercanos → más simple (LogReg > RF > XGBoost); igualdad → cercanos; elegido no supera a Dummy en validación → criterio fallido registrado; complejo no supera a LogReg → conservar LogReg; elegido LogReg → comparar solo con Dummy.

Commit: `feat: preregistered model selection rule`.

## T6 — EXPERIMENTOS Y SELECCIÓN REAL · 1 h 30 min

- Orden: churn-tune → selección pasos 1–2 → E-03 → E-02 → ajuste final → validación pasos 3–4.
- CLI `churn-select` → `reports/model_selection.json`: AP de búsqueda optimista, métricas B media ± std, diferencias pareadas, decisión §6 paso a paso, E-03 con Δ por pliegue/media/decisión, E-02 (a,b,c con n) y AP de validación de candidatos necesarios.
- MLflow: stage ∈ {tuning, reevaluation, experiment, selection}; `final=false`; `experiment=E-02/E-03` donde corresponda.

Commit: `feat: model selection and ablation experiments`.

## T7 — REPORTE Y CIERRE · 1 h

- `reports/model_selection.md` generado desde JSON: tabla B por familia a tres decimales/diferencias pareadas; aplicación de §6 con modelo elegido y motivo; E-03 y decisión según límite preregistrado; E-02 (a,b,c) y lectura para ficha; AP de validación como selección de desarrollo, no estimación final.
- Lenguaje descriptivo, sin causalidad. No hablar de umbrales ni de dinero (semana 5).
- README: tabla de modelos y hoja de ruta. Spec 002 §8: marcar criterios cumplidos.
- Registro: cerrar S08 con comandos, resultados, URL CI y run IDs de MLflow.

Commit: `docs: week 4 model selection and experiments`.

**Al terminar T7: detenerse y esperar revisión. No avanzar a semana 5.**
