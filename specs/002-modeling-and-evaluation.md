# Especificación 002 — Modelado y evaluación

| Campo | Valor |
|---|---|
| Estado | Diseño documentado; implementación pendiente en semanas 3–5 |
| Responsable | Darwin Jacome Cuenca |
| Dependencia | [Especificación 001](001-overview-and-data-contract.md) |
| Versión | v1.1 — incorpora los hallazgos de la semana 2 (spec 003) |
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

- **R1.** Toda transformación con parámetros aprendidos de los datos (medias, escalas, categorías) es un transformador sklearn dentro del Pipeline. Prohibido calcular estadísticos fuera del pipeline. `config.centered_age()` queda solo para la inferencia de la spec 003, nunca en modelado.
- **R2.** Las transformaciones sin estado (`has_balance`, clip de NumOfProducts) usan constantes fijas.
- **R3.** Sin remuestreo (SMOTE, undersampling) ni `class_weight`: las probabilidades deben conservar la escala real para la calibración y la decisión económica (specs 002 §5.3 y 004).
- **R4.** Q-10: `has_balance` y `Geography` comparten señal. Sus coeficientes LogReg no se interpretan por separado; en la semana 6, SHAP se reporta agrupando ambas.
- **R5.** `age_band` deja de ser candidata en modelos lineales; la sustituye el término cuadrático (H4). Los árboles (semana 4) usan Age sin transformar.

`RowNumber`, `CustomerId` y `Surname` se excluyen. `Gender` se conserva exclusivamente para auditoría: nunca se incorpora como feature, tampoco en experimentos ni mediante variables derivadas. E-01 compara resultados por grupos sin entrenar con `Gender`. `EstimatedSalary` permanece como candidata hasta E-03; la variante que la excluya también excluirá `balance_to_salary` para evitar conservar indirectamente su información.

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

## 5. Protocolo de evaluación

### 5.1. Validación cruzada y trazabilidad

- `StratifiedKFold` de 5 pliegues sobre entrenamiento, con mezcla, semilla 42 e idénticas particiones para comparar modelos.
- Reportar **media ± desviación estándar muestral** entre pliegues para cada métrica de la tabla de comparación.
- Ajuste acotado con `RandomizedSearchCV`: como máximo 50 iteraciones por búsqueda, espacio pequeño y documentado, semilla fija y `scoring="average_precision"`.
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
- Etiquetas: `stage=baseline`, `git_commit`, `csv_sha256`, `split_manifest_sha256`, `eligible` (`false` para Dummy) y `final=false`.
- Los tests usan tracking URI temporal en `tmp_path` y no escriben en el directorio `mlruns/` del proyecto.

## 6. Regla de selección del modelo, fijada antes de entrenar

1. Obtener el mayor promedio de AP en validación cruzada entre LogReg, RF y XGBoost; Dummy es únicamente una referencia mínima.
2. Considerar cercanos los candidatos cuya diferencia respecto al mejor promedio sea menor que la desviación estándar del mejor candidato. Si los promedios son iguales, también se consideran cercanos. Elegir entre ellos el más simple: LogReg, luego RF, luego XGBoost. Esta es una heurística de parsimonia, no una prueba de significación estadística.
3. Comprobar en validación que el candidato elegido supera a Dummy en AP. Si no lo supera, registrar el fallo del criterio y revisar el desarrollo sin consultar prueba.
4. Si se elige RF o XGBoost, exigir además que supere a LogReg en AP de validación. Si no lo logra, conservar LogReg siempre que supere a Dummy; de lo contrario, el criterio de aceptación queda sin cumplir.
5. Si se elige LogReg, compararla con Dummy y reportar las diferencias frente a los modelos complejos; no exigir que supere a sí misma.

Registrar cada aplicación de esta regla en MLflow. La selección en validación no reemplaza la evaluación final en prueba.

## 7. Experimentos requeridos

| ID | Experimento | Pregunta |
|---|---|---|
| E-01 | Auditoría de equidad por `Gender`, siempre excluido de las features | ¿Qué diferencias de rendimiento, calibración y decisiones aparecen entre grupos? El costo predictivo de excluirlo no se estima porque no se entrena un modelo con esa variable |
| E-02 | Con y sin la información de `NumOfProducts` | ¿Cuánto depende el modelo del patrón Q-03? La ablación completa se complementará con análisis separado de los clientes con 3–4 productos |
| E-03 | Con y sin `EstimatedSalary` y sus derivadas | ¿Aporta utilidad en combinación con otras variables o introduce ruido? |
| E-04 | Probabilidad original frente a calibración isotónica y sigmoidal | ¿Se reduce Brier en validación con calibradores ajustados únicamente en entrenamiento? |

Los experimentos usarán las mismas particiones y semillas. Cada conclusión incluirá métricas, tamaño de los segmentos pertinentes y limitaciones. Las decisiones de variables se fijarán antes de la evaluación final.

## 8. Criterios de aceptación

- [ ] Tabla de comparación en el README con media ± desviación estándar y protocolo de cálculo.
- [ ] Experimentos E-01 a E-04 documentados con resultados y conclusión breve.
- [ ] División reproducible y ausencia de solapamientos verificada mediante tests.
- [ ] Modelo seleccionado conforme a §6 y calibración conforme a §5.3; decisiones registradas en MLflow.
- [ ] Conjunto de prueba utilizado en una única evaluación final, registrada con la etiqueta `final=true`.
- [ ] Artefacto guardado: pipeline completo, calibrador elegido si aplica y `metadata.json`, con variables, versiones, hash de datos y referencia a la política de decisión.

## 9. Definición de cierre

Modelo y calibración justificados, experimentos documentados y artefacto cargable por el futuro módulo `predict.py`, con un test de predicción reproducible. La capa de decisión y su umbral monetario deberán satisfacer además la especificación 004. La evidencia y los pendientes se mantendrán en el [registro de avance](../docs/registro-avance.md).

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
