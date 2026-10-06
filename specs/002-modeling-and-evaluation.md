# Especificación 002 — Modelado y evaluación

| Campo | Valor |
|---|---|
| Estado | En implementación: semanas 3–4 completadas; calibración (semana 5) pendiente |
| Responsable | Darwin Jacome Cuenca |
| Dependencia | [Especificación 001](001-overview-and-data-contract.md) |
| Versión | v1.4 — aclaración previa a resultados: origen de las OOF de E-02 y ajuste de Dummy en validación; §6 y umbral de E-03 sin cambios |
| Última revisión documental | 6 de octubre de 2026 |

## 1. Objetivo

Seleccionar un modelo que **ordene adecuadamente el riesgo y produzca probabilidades calibradas**, como entrada de la futura capa de decisión por beneficio esperado (especificación 004). La selección prioriza calidad de ordenamiento, calibración y simplicidad; el umbral de contacto se justificará mediante beneficio, no mediante F1.

## 2. División de datos

| Conjunto | Proporción | Uso |
|---|---|---|
| Entrenamiento | 60 % | Ajuste de pipelines, validación cruzada, hiperparámetros y ajuste de calibradores mediante predicciones fuera de muestra |
| Validación | 20 % | Comprobación del modelo seleccionado, comparación de calibración y elección del umbral de decisión |
| Prueba | 20 % | **Una evaluación final**, con todas las decisiones ya fijadas |

- División estratificada por `Exited`, con `random_state = 42`.
- Guardar índices en `data/processed/`, junto con el hash del dataset; comprobar ausencia de solapamiento entre conjuntos.
- Todo preprocesamiento se implementará dentro de un `sklearn.Pipeline`. En validación cruzada, se ajustará únicamente con la partición de entrenamiento de cada pliegue.
- El conjunto de prueba no se usará para crear variables, seleccionar modelos, ajustar calibración ni elegir umbrales. El acceso exploratorio previo al dataset completo se documentará como limitación.
- La validación es un conjunto de desarrollo: las métricas empleadas para elegir calibración o umbral no son estimaciones finales independientes. Estas se obtendrán en prueba.

## 3. Preprocesamiento y variables

| Conjunto | Uso | Definición |
|---|---|---|
| FS-RAW | Referencia ingenua | CreditScore, Age, Tenure, Balance, EstimatedSalary, NumOfProducts (entero), HasCrCard, IsActiveMember, Geography (one-hot, `handle_unknown="error"`). Numéricas con `StandardScaler` en modelos lineales |
| FS-EDA | LogReg informada por H1–H6 | FS-RAW con estos cambios: NumOfProducts → one-hot de {1, 2, 3–4} (H2: no monótona; mapeo sin estado `clip(upper=3)`); Age → `StandardScaler` + término cuadrático, ajustados dentro de cada pliegue (H4); se añade `has_balance` (H5, Q-10); Balance continuo escalado; EstimatedSalary se mantiene hasta E-03 |
| FS-TREE | RF y XGBoost | CreditScore, Age, Tenure, Balance, EstimatedSalary, NumOfProducts (entero, sin agrupar: los árboles modelan la no monotonía), HasCrCard, IsActiveMember, Geography (one-hot) + has_balance. Sin escalado ni término cuadrático |

- **R1.** Toda transformación con parámetros aprendidos de los datos (medias, escalas, categorías) es un transformador sklearn dentro del Pipeline. Prohibido calcular estadísticos fuera del pipeline. `config.centered_age()` queda solo para la inferencia de la spec 003, nunca en modelado.
- **R2.** Las transformaciones sin estado (`has_balance`, clip de NumOfProducts) usan constantes fijas.
- **R3.** Sin remuestreo (SMOTE, undersampling) ni `class_weight`: las probabilidades deben conservar la escala real para la calibración y la decisión económica (specs 002 §5.3 y 004). Aplica también a árboles: `class_weight=None`, `scale_pos_weight=1` y sin remuestreo.
- **R4.** Q-10: `has_balance` y `Geography` comparten señal. Sus coeficientes LogReg no se interpretan por separado; en la semana 6, SHAP se reporta agrupando ambas.
- **R5.** `age_band` deja de ser candidata en modelos lineales; la sustituye el término cuadrático (H4). Los árboles (semana 4) usan Age sin transformar.

`RowNumber`, `CustomerId` y `Surname` se excluyen. `Gender` se conserva exclusivamente para auditoría: nunca se incorpora como feature, tampoco en experimentos ni mediante variables derivadas. E-01 compara resultados por grupos sin entrenar con `Gender`. `EstimatedSalary` permanece como candidata hasta E-03. `balance_to_salary` deja de ser candidata (H6: el salario no tiene señal univariada; E-03 decide sobre el salario). `age_band` ya se había descartado en modelos lineales (R5).

## 4. Modelos

| Orden | Modelo | Propósito |
|---|---|---|
| 0 | `DummyClassifier(strategy="prior")` | Referencia mínima |
| 1 | Regresión logística (LogReg) | Referencia interpretable y candidata válida para selección |
| 2 | Random Forest (RF) | Referencia no lineal |
| 3 | XGBoost | Candidato de árboles con boosting |

Las redes neuronales quedan fuera del alcance del proyecto para mantener un experimento acotado con 10.000 filas tabulares.

Configuración fija de la semana 3, sin ajuste de hiperparámetros:

- Dummy: `DummyClassifier(strategy="prior")` con FS-RAW.
- LogReg: penalización L2, `C=1.0`, `solver="lbfgs"`, `max_iter=1000`, con FS-RAW y con FS-EDA.
- En total, tres corridas: `dummy-raw`, `logreg-raw` y `logreg-eda`. La selección corresponde a la semana 4 (§6).

Espacios de búsqueda de la semana 4, fijados antes de entrenar y expresados mediante distribuciones de `scipy.stats` donde corresponda:

- **LogReg (FS-EDA):** `C ~ loguniform(1e-3, 1e2)`; L2, lbfgs, `max_iter=2000`.
- **RF (FS-TREE):** `n_estimators=500` fijo; `max_depth ∈ {None, 4, 6, 8, 10, 12, 16}`; `min_samples_leaf ∈ {1, 2, 5, 10, 20, 50}`; `max_features ∈ {"sqrt", 0.3, 0.5, 0.8}`; `random_state=42`; `n_jobs=-1`.
- **XGBoost (FS-TREE):** `n_estimators ∈ {100, 200, 400, 800}`; `learning_rate ~ loguniform(0.01, 0.3)`; `max_depth ∈ {2, 3, 4, 5, 6}`; `min_child_weight ∈ {1, 3, 5, 10}`; `subsample ~ uniform(0.6, 0.4)`; `colsample_bytree ~ uniform(0.6, 0.4)`; `reg_lambda ~ loguniform(0.1, 10)`; `tree_method="hist"`; `scale_pos_weight=1`; `eval_metric="logloss"`; `random_state=42`; `n_jobs=-1`. Sin early stopping.

## 5. Protocolo de evaluación

### 5.1. Validación cruzada y trazabilidad

- `StratifiedKFold` de 5 pliegues sobre entrenamiento, con mezcla, semilla 42 e idénticas particiones para comparar modelos.
- Reportar **media ± desviación estándar muestral** entre pliegues para cada métrica de la tabla de comparación.
- **FASE A (ajuste):** `RandomizedSearchCV` sobre entrenamiento con `StratifiedKFold(5, shuffle=True, random_state=42)`, `scoring="average_precision"`, `refit=False`. Presupuestos: LogReg 20 iteraciones, RF 40 y XGBoost 40; `random_state=42` en la búsqueda.
- **FASE B (selección):** la mejor configuración de cada familia se reevalúa en pliegues nuevos: `RepeatedStratifiedKFold(n_splits=5, n_repeats=2, random_state=2027)`, idénticos para todas las familias. La regla de §6 usa las AP medias de FASE B, no las de búsqueda.
- Motivo de las dos fases: el máximo elegido en la búsqueda está inflado por seleccionar entre muchas configuraciones, especialmente en familias con más parámetros. Los nuevos pliegues reducen ese sesgo optimista; la evaluación sigue siendo de desarrollo.
- Reporte adicional informativo: diferencia pareada de AP por pliegue de FASE B entre cada familia y la mejor. No modifica la regla de §6, que permanece congelada.
- Registrar en MLflow parámetros, métricas, semilla, particiones, commit de Git y hash de datos.
- Las métricas de pliegues reutilizados para ajustar hiperparámetros son estimaciones de desarrollo y pueden ser optimistas. Identificarlas como tales; la evaluación final independiente corresponde a prueba.
- La semana 3 evalúa **solo** con validación cruzada estratificada de 5 pliegues sobre entrenamiento (6.000 filas; `shuffle=True`; semilla 42; mismos pliegues para todos los modelos). La validación no se usa en la semana 3.
- Métricas por pliegue: AP (principal), ROC-AUC, Brier y log loss. Reporte: media ± desviación estándar muestral (`ddof=1`). El ajuste acotado indicado arriba corresponde a la semana 4, no a las baselines fijas.

### 5.2. Métricas

| Rol | Métrica | Justificación |
|---|---|---|
| Principal | Precisión promedio (AP, `average_precision_score`) | Calidad de ordenamiento de la clase positiva con objetivo desbalanceado |
| Secundaria | ROC-AUC | Ordenamiento global |
| Calibración | Puntuación de Brier y curva de fiabilidad | Las probabilidades alimentan decisiones monetarias |
| Reporte final | Precisión, sensibilidad (recall), F1 y matriz de confusión al umbral elegido | Interpretación de la política fijada por beneficio |

Cuando se use la etiqueta PR-AUC en resultados, se indicará que corresponde a **AP**, no a integración trapezoidal de la curva precisión-sensibilidad. Las métricas que requieren umbral en la tabla inicial usarán 0,5, identificado como referencia técnica; el umbral operativo se fijará en la semana 5.

### 5.3. Calibración sin solapamiento de ajuste y evaluación

La calibración se implementará en la semana 5, una vez seleccionado el modelo:

1. Con hiperparámetros fijados, generar predicciones fuera de muestra (OOF) en entrenamiento mediante 5 pliegues estratificados. Cada observación se predice con un pipeline que no se ajustó con ella.
2. Ajustar los calibradores sigmoidal e isotónico con esas predicciones OOF y las etiquetas de entrenamiento. Después, ajustar el pipeline base con todo el entrenamiento.
3. Comparar la salida sin calibrar y las variantes calibradas en validación mediante Brier y curvas de fiabilidad. Elegir la variante con menor Brier; ante igualdad, preferir sin calibración adicional y luego sigmoidal sobre isotónica.
4. Fijar en validación el umbral por beneficio esperado según la especificación 004. No ajustar el calibrador con las etiquetas de validación.
5. Congelar pipeline, calibrador, supuestos y umbral antes de la evaluación final en prueba. No reajustar con validación antes de esa evaluación.

El uso de validación para elegir calibración y umbral se registrará como selección de desarrollo, no como medición independiente de rendimiento.

### 5.4. Trazabilidad en MLflow

- Tracking URI desde `MLFLOW_TRACKING_URI`; por defecto `sqlite:///mlruns/mlflow.db` (`mlruns/` fuera de Git). Experimento: `bank-churn`.
- Parámetros: modelo, conjunto de variables, hiperparámetros, `n_folds`, `seed`.
- Métricas: media y desviación de cada métrica, más las métricas por pliegue con `step` igual al número de pliegue.
- Etiquetas: `stage=baseline` para semana 3 y `stage ∈ {tuning, reevaluation, experiment, selection}` para semana 4, `git_commit`, `csv_sha256`, `split_manifest_sha256`, `eligible` (`false` para Dummy) y `final=false`. En experimentos, etiqueta `experiment=E-02` o `experiment=E-03` donde corresponda. El puntaje de búsqueda se marca como optimista.
- Los tests usan tracking URI temporal en `tmp_path` y no escriben en el directorio `mlruns/` del proyecto.

## 6. Regla de selección del modelo, fijada antes de entrenar

1. Obtener el mayor promedio de AP en validación cruzada entre LogReg, RF y XGBoost; Dummy es únicamente una referencia mínima.
2. Considerar cercanos los candidatos cuya diferencia respecto al mejor promedio sea menor que la desviación estándar del mejor candidato. Si los promedios son iguales, también se consideran cercanos. Elegir entre ellos el más simple: LogReg, luego RF, luego XGBoost. Esta es una heurística de parsimonia, no una prueba de significación estadística.
3. Comprobar en validación que el candidato elegido supera a Dummy en AP. Si no lo supera, registrar el fallo del criterio y revisar el desarrollo sin consultar prueba.
4. Si se elige RF o XGBoost, exigir además que supere a LogReg en AP de validación. Si no lo logra, conservar LogReg siempre que supere a Dummy; de lo contrario, el criterio de aceptación queda sin cumplir.
5. Si se elige LogReg, compararla con Dummy y reportar las diferencias frente a los modelos complejos; no exigir que supere a sí misma.

Registrar cada aplicación de esta regla en MLflow. La selección en validación no reemplaza la evaluación final en prueba.

En semana 4, los pasos 1–2 utilizan las AP medias y desviación estándar de **FASE B**. Los pasos 1–5 anteriores permanecen congelados, sin reinterpretación.

**Uso de validación por primera vez en el modelado:** solo para los pasos 3–4. Cada candidato necesario se ajusta con todo el entrenamiento y se calcula su AP en validación una vez, registrada en MLflow con `stage=selection`. No se ajustan hiperparámetros ni variables con validación.

**Orden de ejecución fijo:** FASE A → FASE B → aplicar §6 pasos 1–2 → E-03 (decide conjunto final de variables) → E-02 (auditoría) → ajustar en entrenamiento con el conjunto final → validación, pasos 3–4 (el candidato y, si es complejo, LogReg con la misma decisión de variables).

## 7. Experimentos requeridos

| ID | Experimento | Pregunta |
|---|---|---|
| E-01 | Auditoría de equidad por `Gender`, siempre excluido de las features | ¿Qué diferencias de rendimiento, calibración y decisiones aparecen entre grupos? El costo predictivo de excluirlo no se estima porque no se entrena un modelo con esa variable |
| E-02 | Con y sin la información de `NumOfProducts` | ¿Cuánto depende el modelo del patrón Q-03? La ablación completa se complementará con análisis separado de los clientes con 3–4 productos |
| E-03 | Con y sin `EstimatedSalary` y sus derivadas | ¿Aporta utilidad en combinación con otras variables o introduce ruido? |
| E-04 | Probabilidad original frente a calibración isotónica y sigmoidal | ¿Se reduce Brier en validación con calibradores ajustados únicamente en entrenamiento? |

Los experimentos usarán las mismas particiones y semillas. Cada conclusión incluirá métricas, tamaño de los segmentos pertinentes y limitaciones. Las decisiones de variables se fijarán antes de la evaluación final.

Decisiones preregistradas de semana 4: sobre la familia seleccionada, con sus hiperparámetros fijos, sin reajuste de hiperparámetros y en los pliegues de FASE B:

- **E-03:** comparar con y sin `EstimatedSalary`. Δ = AP(sin) − AP(con), pareada por pliegue. Si media(Δ) ≥ −0,005, eliminar `EstimatedSalary` del modelo final por parsimonia; en caso contrario conservarlo.
- **E-02:** auditoría, no decisión de eliminar `NumOfProducts`, cuya señal está documentada en H2. Reportar (a) AP con/sin `NumOfProducts`, pareada; (b) con predicciones OOF de FASE B, AP excluyendo clientes con `NumOfProducts ≥ 3` para medir rendimiento sin el grupo fácil del artefacto Q-03; (c) en el grupo 3–4, probabilidad media predicha frente a tasa observada, con n. Alimenta la ficha del modelo de semana 6.
  - Unidad de cálculo para (b) y (c): la repetición. En cada repetición de FASE B cada cliente de entrenamiento tiene exactamente una predicción OOF; las métricas se calculan sobre las predicciones de esa repetición. Se reportan los valores de cada repetición y su media.
  - Prohibido: (1) promediar probabilidades por cliente entre repeticiones (genera un ensamble distinto del modelo evaluado); (2) juntar las predicciones de ambas repeticiones (duplica a cada cliente).
  - (b) se compara con la AP de todos los clientes calculada de la misma forma, agregada por repetición, no con la media por pliegue de FASE B.
  - n = número de clientes únicos del segmento en entrenamiento, igual en ambas repeticiones. Las OOF se guardan con `CustomerId`, `repeat` (0/1), `fold`, `y` y `proba`.
  - Aclaración v1.4 (antes de ejecutar E-02 con datos reales): E-02 audita la **configuración final**, es decir, después de la decisión de E-03. (a) compara esa configuración con y sin `NumOfProducts` en los pliegues de FASE B. (b) y (c) usan sus OOF de FASE B: si E-03 elimina el salario, las OOF de la re-evaluación sin salario (mismos pliegues); si no, las OOF de FASE B de la familia elegida.
  - Validación (pasos 3–4): Dummy se ajusta con FS-RAW sobre todo el entrenamiento; el candidato y, si es complejo, LogReg usan sus mejores hiperparámetros de FASE A y la misma decisión de E-03.

## 8. Criterios de aceptación

- [x] Tabla de comparación en el README con media ± desviación estándar y protocolo de cálculo (semanas 3–4).
- [ ] Experimentos E-01 a E-04 documentados con resultados y conclusión breve.
- [x] División reproducible y ausencia de solapamientos verificada mediante tests.
- [ ] Modelo seleccionado conforme a §6 y calibración conforme a §5.3; decisiones registradas en MLflow.
- [ ] Conjunto de prueba utilizado en una única evaluación final, registrada con la etiqueta `final=true`.
- [ ] Artefacto guardado: pipeline completo, calibrador elegido si aplica y `metadata.json`, con variables, versiones, hash de datos y referencia a la política de decisión.

## 9. Definición de cierre

Modelo y calibración justificados, experimentos documentados y artefacto cargable por el futuro módulo `predict.py`, con un test de predicción reproducible. La capa de decisión y su umbral monetario deberán satisfacer además la especificación 004. La evidencia y los pendientes se mantendrán en el [registro de avance](../docs/registro-avance.md).

Prueba de referencia B-02 para AP por repetición:

| Objetivo | Repetición 1 | Repetición 2 | AP rep1 | AP rep2 | Media |
|---|---|---|---|---|---|
| y=[0,1,0,1] | [0.1,0.9,0.7,0.6] | [0.8,0.7,0.2,0.5] | 0,833333 | 0,583333 | 0,708333 |

## 10. Alcance de implementación de la semana 3

El [plan de semana 3](../docs/plan-semana-3.md) fija T0–T7. La enmienda v1.1 incorpora los siguientes entregables aprobados:

- Deuda de presentación: formateadores de miles y porcentajes, un color, títulos H1–H6, layout de paneles y umbral de OR=1,5; regenerar las seis figuras sin cambiar datos ni cálculos.
- Dependencia `mlflow`. Si su tamaño rompe CI, detenerse y proponer `mlflow-skinny` mediante un bloqueo; no sustituirla sin decisión.
- `features.py`: `HasBalance` y `ProductsGroup`, transformadores sklearn sin estado y con `get_feature_names_out`; edad cuadrática mediante `StandardScaler` seguido de `PolynomialFeatures(degree=2, include_bias=False)`. `FEATURE_SETS` en config contiene las columnas de entrada `raw` y `eda`, excluyendo auditoría e IDs.
- `pipeline.py`: `build_pipeline(model, feature_set)` devuelve un `sklearn.Pipeline` con `ColumnTransformer` y modelo; `model` en {dummy, logreg}, `feature_set` en {raw, eda}. Un DataFrame con `Gender` produce `ValueError` antes de modelar; no se descarta silenciosamente. Categorías desconocidas de Geography producen error.
- `train.py`: `load_training()` filtra `load_exploration()` a `partition == "train"`; no existen lectores de prueba ni de validación para entrenar. `cross_validate_model(pipeline, X, y)` devuelve métricas por pliegue y resumen; `log_run(...)` registra §5.4.
- CLI `churn-baselines`: ejecuta exclusivamente las tres corridas fijadas y escribe `reports/baselines.json`. `reports/baselines.md` se genera desde ese JSON y presenta modelo × {AP, ROC-AUC, Brier, log loss}, con media ± desviación estándar.
- Tests de transformadores sin estado/no fuga, pipelines/probabilidades/categorías/columnas prohibidas, métricas Dummy, determinismo y mismos pliegues, exclusión de clientes de validación/prueba de entrenamiento y trazabilidad MLflow temporal.
- Cierre: 3–5 líneas descriptivas sobre la diferencia de AP frente a las desviaciones estándar, sin seleccionar modelo; README y S07 actualizados, CI verificado y corridas MLflow localizadas. Detenerse para revisión tras T7.

## 11. Alcance de implementación de la semana 4

El [plan completo de semana 4](../docs/plan-semana-4.md) fija T0–T7 y las observaciones O1–O3:

- O1/O2: reportes legibles de baselines a tres decimales y diferencia pareada EDA−RAW de AP por pliegue (media, std ddof=1 y signo). Generar desde JSON y probar diferencias sobre JSON sintético; cambios de código de reportes corresponden a T1, después de T0.
- T2: añadir `xgboost`, bloquear dependencias y sincronizar todos los grupos.
- T3: ampliar `build_pipeline` a modelos {rf, xgb} con feature_set `tree`, manteniendo InputGuard; espacios exactos de §4 en `search_spaces.py`. Tests de coincidencia exacta, probabilidades, ausencia de escalado/ponderación y determinismo con la misma semilla.
- T4: `tune.py`, `tune_family(family)` para FASE A exclusivamente con `load_training()`, y `reevaluate(configs)` para FASE B. Métricas por pliegue AP, ROC-AUC, Brier y log loss; guardar OOF en `data/processed/oof_phaseB.parquet`, fuera de Git. CLI `churn-tune` → `reports/tuning.json`. Tests sintéticos con presupuesto reducido y pliegues B iguales entre familias, diferentes de A, sin validación externa.
- T5: `selection.py`, función pura `select_model(cv_summary, val_scores=None)` que aplica literalmente §6 pasos 1–5. Tests de todas las ramas, incluido fallo frente a Dummy, fallback a LogReg y comparación de LogReg solo con Dummy.
- T6: CLI `churn-select` → `reports/model_selection.json`, con AP de búsqueda optimista, métricas FASE B, diferencias pareadas, decisiones paso a paso, E-03, E-02 y AP de validación de los candidatos necesarios, siguiendo el orden de §6. Registrar stages y etiquetas de §5.4.
- T7: `reports/model_selection.md` generado desde JSON, tablas a tres decimales, aplicación de la regla, experimentos y AP de validación como selección de desarrollo; lenguaje descriptivo sin causalidad y sin decisiones económicas de semana 5. README, criterios cumplidos de §8 y S08 actualizados con CI y run IDs. Detenerse para revisión, sin avanzar a semana 5.
