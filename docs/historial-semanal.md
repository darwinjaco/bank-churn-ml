# Historial semanal del proyecto

Resúmenes por semana que acompañaban al README durante el desarrollo (semanas 1–7). Se conservan como historial; el estado actual está en el [README](../README.md) y el detalle verificable en el [registro de avance](registro-avance.md). Los comandos se ejecutan desde la raíz del repositorio.

## Calidad de datos (semana 1)

Estos valores proceden de [`reports/data_quality.json`](../reports/data_quality.json), reproducido con el CSV local el 6 de octubre de 2026 sin diferencias respecto al reporte inicial.

| Comprobación | Resultado registrado |
|---|---|
| Filas / duplicados según el reporte | 10.000 / 0 |
| Tasa de abandono | 20,37 %: clases desbalanceadas |
| `Balance = 0` | 36,17 %: masa puntual en cero |
| Abandono con 3 productos | 82,71 % en 266 clientes |
| Abandono con 4 productos | 100 % en 60 clientes |
| `EstimatedSalary` | AUC individual de 0,5087; 59 valores menores a 1.000 |
| Alarma de fuga por AUC individual | Ninguna variable numérica alcanza `max(AUC, 1 − AUC) ≥ 0,90`; máximo: `Age`, 0,7321 |

Los patrones de productos y salarios motivan una auditoría de posible origen sintético, pero no lo demuestran. La alarma univariada tampoco descarta todas las formas de fuga de información. El CSV pasó el contrato y la comprobación adicional confirmó cero valores nulos.

`RowNumber`, `CustomerId` y `Surname` están excluidos de las entradas del modelo. `Gender` se conserva exclusivamente para auditoría y nunca se usa como feature, tampoco en experimentos. `EstimatedSalary` sigue como candidata en la configuración; su exclusión se decidirá mediante el experimento E-03, no solo por su AUC individual.

## Semana 2: hipótesis preregistradas

Las seis hipótesis cumplieron sus criterios sobre **8.000 clientes de entrenamiento + validación**, con IC del 95 % y Holm solo sobre H1–H5. La evaluación final del conjunto de prueba sigue reservada.

| Hipótesis | Resultado principal |
|---|---|
| H1: inactividad | DR +12,27 pp [10,51; 14,03] |
| H2: productos no monótonos | Tasas 2 < 1 < 3–4: 7,38 % < 27,98 % < 85,60 %, IC no solapados |
| H3: Alemania ajustada por saldo | OR 2,1787 [1,9133; 2,4809] |
| H4: edad en U invertida | β cuadrático −0,003429; pico puntual 56,58 años |
| H5: saldo cero | DR −10,62 pp [−12,31; −8,88] |
| H6: equivalencia de AUC salarial | AUC 0,5146 [0,4997; 0,5306], dentro del margen [0,45; 0,55] |

Estas asociaciones no prueban causalidad, origen sintético ni utilidad predictiva del modelo. H6 no descarta interacciones del salario. El [reporte completo](../reports/eda_hypotheses.md) contiene p-valores, pruebas usadas, límites e implicaciones para E-02/E-03.

Reproducir EDA, después de colocar el CSV:

```powershell
uv sync --locked --all-groups
uv run churn-split
uv run churn-hypotheses
uv run --group eda python -m churn.plots
```

El [manifiesto](../reports/split_manifest.json) está versionado; `data/processed/split.json` está excluido de Git. El [notebook](../notebooks/01_eda.ipynb) carga solo exploración y muestra resultados/figuras, con salidas eliminadas.

## Semana 3: baselines y MLflow

Cinco pliegues estratificados comunes sobre **6.000 filas de entrenamiento**, con mezcla y semilla 42. Media ± desviación estándar muestral (`ddof=1`); hiperparámetros fijos, sin ponderación ni remuestreo.

| Modelo | AP | ROC-AUC | Brier | Log loss |
|---|---|---|---|---|
| dummy-raw | 0.204 ± 0.000 | 0.500 ± 0.000 | 0.162 ± 0.000 | 0.506 ± 0.001 |
| logreg-raw | 0.459 ± 0.029 | 0.755 ± 0.012 | 0.138 ± 0.004 | 0.435 ± 0.009 |
| logreg-eda | 0.657 ± 0.028 | 0.839 ± 0.021 | 0.111 ± 0.005 | 0.364 ± 0.018 |

FS-RAW es la referencia ingenua. FS-EDA agrupa productos 3–4 antes de one-hot, añade `has_balance` y transforma edad con escala/cuadrática aprendidas dentro de cada pliegue; el salario se conserva hasta E-03. `centered_age()` permanece solo en inferencia de EDA. Se mantiene la lectura conjunta de saldo y geografía de Q-10.

La diferencia pareada de AP entre las dos LogReg es **+0,198 ± 0,019**, positiva en los cinco pliegues; es una lectura descriptiva, sin selección de modelo. Validación y prueba se reservan para sus fases posteriores. Detalles, procedencia y run IDs en [baselines.md](../reports/baselines.md) y [baselines.json](../reports/baselines.json).

Después de colocar el CSV y disponer de la división:

```powershell
uv run churn-baselines
uv run mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db --port 5000
```

La interfaz está en `http://127.0.0.1:5000`; experimento `bank-churn`, tracking por defecto `sqlite:///mlruns/mlflow.db`, configurable con `MLFLOW_TRACKING_URI`. Las corridas usan `stage=baseline`, `final=false` y Dummy `eligible=false`. `mlruns/` está excluido de Git.

## Cronograma

Plan del **5 de octubre al 29 de noviembre de 2026**, con unas **8 horas por semana**. Las fechas son objetivos; los cierres reales se registran en [docs/registro-avance.md](registro-avance.md).

| Semana | Fechas | Entregable | Criterio de cierre |
|---|---|---|---|
| 1 | 5–11 oct | Repo, uv, Ruff, pytest, pre-commit, CI mínimo, specs 001–002 y validación con Pandera | Tests pasan en CI |
| 2 | 12–18 oct | EDA, hipótesis y auditoría de productos 3–4 y balance cero | Hipótesis contrastadas con pruebas estadísticas, tamaños de efecto e incertidumbre |
| 3 | 19–25 oct | Pipeline, división estratificada, Dummy/LogReg y MLflow | Modelos de referencia registrados en MLflow |
| 4 | 26 oct–1 nov | Random Forest, XGBoost, validación cruzada y ajuste acotado | Tabla de media ± desviación estándar por modelo |
| 5 | 2–8 nov | Calibración y umbral analítico por beneficio esperado (opción A) | Umbral justificado en dinero bajo supuestos explícitos |
| 6 | 9–15 nov | SHAP, errores, segmentos y ficha del modelo (model card) | Limitaciones documentadas |
| 7 | 16–22 nov | FastAPI, Streamlit, tests de API y Docker Compose | `docker compose up` funciona desde cero |
| 8 | 23–29 nov | Cambio de distribución simulado con Evidently, despliegue y README con resultados | URL pública y reproducibilidad verificadas |

**Prioridad:** la capa de decisión de la semana 5 es el entregable central. Si hay retrasos, se reduce primero el alcance del monitoreo de cambios de distribución de la semana 8.

## Semana 4: selección de modelo y ablaciones

Ajuste en dos fases (spec 002 v1.4): FASE A busca hiperparámetros (`RandomizedSearchCV`, 5 pliegues, semilla 42); FASE B re-evalúa la mejor configuración de cada familia en pliegues **nuevos** 5×2 (semilla 2027) para reducir el sesgo optimista de la búsqueda. La regla de selección se fijó antes de entrenar.

| Familia | AP FASE B | ROC-AUC | Brier | AP validación |
|---|---|---|---|---|
| LogReg (FS-EDA) | 0.655 ± 0.027 | 0.839 ± 0.010 | 0.111 ± 0.004 | 0.637 |
| Random Forest (FS-TREE) | 0.686 ± 0.018 | 0.854 ± 0.012 | 0.106 ± 0.003 | 0.696 |
| XGBoost (FS-TREE) | 0.697 ± 0.018 | 0.860 ± 0.010 | 0.106 ± 0.003 | — |
| Dummy (FS-RAW) | — | — | — | 0.203 |

- **Selección (§6):** XGBoost tiene la mayor AP, pero Random Forest queda a 0.011, menos que la desviación del mejor (0.018); por parsimonia se elige **Random Forest**. En validación supera a Dummy y a LogReg.
- **E-03 (salario):** quitar `EstimatedSalary` cambia la AP en +0.003 ± 0.004; con el umbral preregistrado (Δ ≥ −0,005) se **elimina**, coherente con H6.
- **E-02 (productos):** sin `NumOfProducts` la AP cae -0.113. El 3.4% de clientes con 3–4 productos aporta 0.079 de AP: sin ese grupo la AP es 0.608. En ese grupo el modelo predice 73.2% frente a 87.1% observado: insumo para la calibración de la semana 5.

Métricas de desarrollo: la validación se usó para elegir. Detalle, regla paso a paso y run IDs en [model_selection.md](../reports/model_selection.md).

```powershell
uv run churn-tune      # FASE A + FASE B (~8 min con 2 núcleos)
uv run churn-select    # regla §6, E-03, E-02 y validación
uv run python -m churn.selection_report
```

## Semana 5: calibración y decisión

E-04 calibra el Random Forest final con predicciones OOF de entrenamiento y compara en validación: Brier sin calibrar 0.1026, **sigmoide 0.1010** (elegida), isotónica 0.1013. La sigmoide corrige la subestimación del decil de mayor riesgo y conserva la AP.

Regla de la spec 004 (opción A): contactar si la probabilidad calibrada supera **t\* = c / (s·V) = 1/6**, con supuestos ilustrativos V = 1.000 €, c = 50 € y s = 30 %. El umbral es analítico, no se ajusta con datos.

| Política (validación, 2.000 clientes) | Contactados | Beneficio |
|---|---|---|
| Nadie | 0 | 0 € |
| Todos | 2.000 | 22.100 € |
| Aleatoria 20 % | 400 | 4.420 € |
| **Modelo** | **621** | **61.950 €** |
| Oráculo (cota superior) | 407 | 101.750 € |

El modelo obtiene 39.850 € más que la mejor política sin modelo y captura el 60.9% del beneficio máximo posible. Cifras de desarrollo con supuestos ilustrativos; detalle y límites en [decision.md](../reports/decision.md).

```powershell
uv run churn-decide                       # E-04, decisión, artefacto en models/ y figura
uv run python -m churn.decision_report
```

## Semana 6: explicabilidad, auditoría y ficha del modelo

Sobre validación, con el artefacto congelado de la semana 5 (spec 002 v1.6 §11):

- **SHAP** (aditividad comprobada): las variables más influyentes son Age, NumOfProducts, IsActiveMember y Geography=Germany, en línea con las hipótesis H1–H4. Importancia predictiva, no causal.
- **Errores:** los abandonos no detectados son clientes más jóvenes y activos; en el tramo 18-29 no se contacta al 65% de quienes se van (n = 26).
- **E-01 (género, solo auditoría):** misma tasa de contacto (31.2% frente a 31.0%) y sensibilidad sin diferencia detectable. **Alerta preregistrada en precisión** (59.6% frente a 42.2%), coherente con tasas base distintas; al excluir `Gender` hay una leve descalibración opuesta por género, bajo el umbral de alerta.

Reportes: [audit.md](../reports/audit.md) y la [ficha del modelo](../reports/model_card.md).

```powershell
uv run churn-audit
uv run python -m churn.model_card
```

## Evaluación final en prueba (única)

Con modelo, calibrador y umbral congelados, sobre 2.000 clientes nunca usados: **AP 0,705**, ROC-AUC 0,862, Brier 0,1017. El modelo contacta a 634 clientes y obtiene **61.600 €**, frente a 22.100 € contactando a todos (60,5 % del máximo posible). Las cifras coinciden con las de validación (AP 0,696; 61.950 €): sin señales de sobreajuste. Detalle en la [ficha del modelo](../reports/model_card.md).

## Semana 7: API, dashboard y Docker

El modelo congelado se sirve con **FastAPI** y un dashboard **Streamlit** que solo consume la API ([spec 005](../specs/005-api-and-dashboard.md)).

| Endpoint | Uso |
|---|---|
| `GET /health` | Estado y SHA-256 del artefacto |
| `GET /model` | Variables, umbral, supuestos y evaluación final |
| `POST /predict` | Probabilidad calibrada, contactar sí/no, beneficio esperado y 3 razones SHAP |
| `POST /predict/batch` | Hasta 1.000 clientes y resumen de contactados y beneficio |
| `POST /explain` | Explicación en texto (LLM opcional; sin clave, plantilla) |

La entrada se valida con el contrato de datos: `Gender` o identificadores devuelven **422**. Documentación interactiva en `/docs`.

**Con Docker** (requiere el Release `model-v1.0`; el build descarga el modelo y verifica su SHA-256):

```powershell
docker compose up --build
# API: http://localhost:8000/docs   Dashboard: http://localhost:8501
```

Verificación automática (build, arranque, `/predict`, 422 con `Gender`, `/explain` y dashboard):

```powershell
pwsh -File scripts/verify-docker.ps1        # añade -Down para detener al final
pwsh -File scripts/verify-docker.ps1 -LocalModel   # sin Release: usa models/model.joblib (mismo SHA-256)
```

**Sin Docker** (con `models/model.joblib` local o descargado con `uv run python -m churn.artifact`):

```powershell
uv run uvicorn churn.api:app --port 8000
uv run streamlit run dashboard/app.py
```

**LLM opcional** para `/explain`: copiar `.env.example` a `.env` (no se versiona) y definir `LLM_BASE_URL`, `LLM_API_KEY` y `LLM_MODEL` de un proveedor compatible con OpenAI (NVIDIA NIM u OpenRouter). Solo se envían las variables del contrato, la probabilidad y las razones, nunca identificadores; ante cualquier fallo se usa la plantilla.

### Publicar el modelo (una vez, responsable del repositorio)

1. En GitHub: **Releases → Draft a new release**, etiqueta `model-v1.0`, título "Modelo congelado v1.0".
2. Adjuntar `models/model.joblib` (SHA-256 `579b7fe349dc035c3171582cbfba1bfaed4599a795da4b149d7664ed21dc095a`) y publicar.
3. Comprobar: `uv run python -m churn.artifact` en un clon sin `models/` descarga y verifica el archivo.

Estado de cierre: semanas 1–5 publicadas y reproducidas desde un clon limpio; semana 6 completada con la evaluación final en prueba (una sola vez); semana 7 implementada (falta publicar el Release y probar `docker compose up`). Semana 8 sin iniciar. La división se adelantó a semana 2 para reservar la prueba antes del EDA.
