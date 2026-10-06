# Abandono bancario → Decisiones de retención

[![CI](https://github.com/darwinjaco/bank-churn-ml/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/darwinjaco/bank-churn-ml/actions/workflows/ci.yml)

Proyecto de aprendizaje automático de extremo a extremo para estimar el abandono de clientes (**churn**) y **decidir a quién conviene contactar**, convirtiendo probabilidades calibradas en beneficio esperado bajo supuestos explícitos.

> En desarrollo. Semanas 1–2 implementadas y verificadas; EDA e hipótesis preregistradas listas para revisión. La semana 3 espera esa revisión. El detalle está en el [registro de avance](docs/registro-avance.md).

## Objetivo de negocio

La pregunta central es: *con un presupuesto de retención, ¿a qué clientes debemos contactar y qué beneficio esperamos frente a no contactar a nadie, contactar a todos o seleccionar clientes al azar?*

El dataset no contiene ingresos del banco, valor de vida del cliente (CLV), costos de campaña ni resultados de intervenciones. Estas cantidades y la eficacia de la retención serán **supuestos documentados**, con análisis de sensibilidad. El beneficio será una estimación por escenarios, no un resultado económico observado ni una estimación causal.

## Estado actual

- Implementados: contrato con Pandera, división estratificada, manifiesto, helpers estadísticos, H1–H6, seis figuras y notebook de EDA.
- Configurados: uv, Ruff, pytest, pre-commit y GitHub Actions; cobertura mínima en CI del 85 %.
- Documentadas: especificaciones 001–003 en español; v1.1 de EDA conserva H1–H6 y fija Freeman–Halton exacto para resolver B-01.
- Verificados localmente: contrato, manifiesto real, Ruff, formato, pre-commit y 71 tests; cobertura del 98,48 %.
- Reglas de trabajo: [AGENTS.md](AGENTS.md), incluidas especificación previa y exclusión permanente de `Gender` de las features.
- Repositorio público: [darwinjaco/bank-churn-ml](https://github.com/darwinjaco/bank-churn-ml), rama `main`.
- CI remoto verificado: 69 tests aprobados, 2 omitidos y 98,05 % de cobertura; [ejecución técnica de semana 2](https://github.com/darwinjaco/bank-churn-ml/actions/runs/37487169164).

Los dos tests con datos reales se omiten en CI porque el CSV se obtiene por separado. Los resultados locales de Windows y remotos de Linux están registrados en S02–S06.

## Inicio rápido

Requisitos: Git y [uv](https://docs.astral.sh/uv/). La versión de referencia es Python 3.11, fijada en `.python-version`; el paquete admite Python `>=3.11,<3.13`.

Para obtener una copia nueva, en PowerShell:

```powershell
git clone https://github.com/darwinjaco/bank-churn-ml.git
Set-Location bank-churn-ml
```

Desde la raíz del proyecto:

```powershell
uv sync --locked --all-groups # Incluye el grupo eda, necesario para los tests gráficos
uv run pre-commit install    # Instala las comprobaciones previas a cada commit
uv run pytest                # Usa datos sintéticos; omite los tests reales si falta el CSV
```

Comprobaciones de calidad (lint, formato y tests también se ejecutan en CI):

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=churn --cov-report=term-missing --cov-fail-under=85
uv run pre-commit run --all-files
```

## Datos

El CSV no se distribuye en el repositorio. La versión esperada de *Churn Modelling* tiene 14 columnas, incluida `Exited`, y **no contiene `Complain`**.

1. Obtén `Churn_Modelling.csv` desde [Kaggle](https://www.kaggle.com/datasets/shrutimechlearn/churn-modelling).
2. Coloca una copia en `data/raw/Churn_Modelling.csv`. Si ya está en Descargas, desde la raíz del proyecto en PowerShell:

   ```powershell
   Copy-Item -LiteralPath "$HOME\Downloads\Churn_Modelling.csv" -Destination "data/raw/Churn_Modelling.csv"
   ```

   Si tienes la CLI de Kaggle instalada y configurada, también puedes descargarlo así:

   ```powershell
   kaggle datasets download -d shrutimechlearn/churn-modelling -p data/raw --unzip
   ```

3. Ejecuta la validación:

   ```powershell
   uv run churn-validate --out reports/data_quality.json
   ```

El [contrato de datos](specs/001-overview-and-data-contract.md) define columnas, tipos, rangos y roles. `.gitignore` excluye los datos originales y procesados; la carga no modifica el CSV.

### Hallazgos del reporte existente

Estos valores proceden de [`reports/data_quality.json`](reports/data_quality.json), reproducido con el CSV local el 6 de octubre de 2026 sin diferencias respecto al reporte inicial.

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

### Semana 2: hipótesis preregistradas

Las seis hipótesis cumplieron sus criterios sobre **8.000 clientes de entrenamiento + validación**, con IC del 95 % y Holm solo sobre H1–H5. La evaluación final del conjunto de prueba sigue reservada.

| Hipótesis | Resultado principal |
|---|---|
| H1: inactividad | DR +12,27 pp [10,51; 14,03] |
| H2: productos no monótonos | Tasas 2 < 1 < 3–4: 7,38 % < 27,98 % < 85,60 %, IC no solapados |
| H3: Alemania ajustada por saldo | OR 2,1787 [1,9133; 2,4809] |
| H4: edad en U invertida | β cuadrático −0,003429; pico puntual 56,58 años |
| H5: saldo cero | DR −10,62 pp [−12,31; −8,88] |
| H6: equivalencia de AUC salarial | AUC 0,5146 [0,4997; 0,5306], dentro del margen [0,45; 0,55] |

Estas asociaciones no prueban causalidad, origen sintético ni utilidad predictiva del modelo. H6 no descarta interacciones del salario. El [reporte completo](reports/eda_hypotheses.md) contiene p-valores, pruebas usadas, límites e implicaciones para E-02/E-03.

Reproducir EDA, después de colocar el CSV:

```powershell
uv sync --locked --all-groups
uv run churn-split
uv run churn-hypotheses
uv run --group eda python -m churn.plots
```

El [manifiesto](reports/split_manifest.json) está versionado; `data/processed/split.json` está excluido de Git. El [notebook](notebooks/01_eda.ipynb) carga solo exploración y muestra resultados/figuras, con salidas eliminadas.

## Estructura del proyecto

```text
docs/         Registro de avance por fases y secciones
specs/        Especificaciones de diseño previas a la implementación
src/churn/    Contrato, división, estadística, hipótesis y figuras
tests/        Tests sintéticos, gráficos headless y dos tests opcionales con CSV real
data/         raw/ y processed/; datos excluidos de Git
reports/      Reportes generados y evidencia de calidad
notebooks/    EDA delgado; lógica reutilizable en src/churn/
```

## Especificaciones previstas

| N.º | Especificación | Estado |
|---|---|---|
| 001 | [Visión general y contrato de datos](specs/001-overview-and-data-contract.md) | Completada: validación local y CI remoto verificados |
| 002 | [Modelado y evaluación](specs/002-modeling-and-evaluation.md) | Documentada; implementación pendiente |
| 003 | [EDA e hipótesis preregistradas](specs/003-eda-and-hypotheses.md) | Implementada v1.1; pendiente de revisión |
| 004 | Capa de decisión y beneficio esperado | Por redactar antes de la semana 5 |
| 005 | API y dashboard | Por redactar antes de la semana 7 |
| 006 | Operación: tests, Docker, CI y monitoreo | Por redactar antes de ampliar operación y serving |

## Cronograma

Plan del **5 de octubre al 29 de noviembre de 2026**, con unas **8 horas por semana**. Las fechas son objetivos; los cierres reales se registran en [docs/registro-avance.md](docs/registro-avance.md).

| Semana | Fechas | Entregable | Criterio de cierre |
|---|---|---|---|
| 1 | 5–11 oct | Repo, uv, Ruff, pytest, pre-commit, CI mínimo, specs 001–002 y validación con Pandera | Tests pasan en CI |
| 2 | 12–18 oct | EDA, hipótesis y auditoría de productos 3–4 y balance cero | Hipótesis contrastadas con pruebas estadísticas, tamaños de efecto e incertidumbre |
| 3 | 19–25 oct | Pipeline, división estratificada, Dummy/LogReg y MLflow | Modelos de referencia registrados en MLflow |
| 4 | 26 oct–1 nov | Random Forest, XGBoost, validación cruzada y ajuste acotado | Tabla de media ± desviación estándar por modelo |
| 5 | 2–8 nov | Calibración, umbral por beneficio esperado, lift y beneficio por decil, sensibilidad | Umbral justificado en dinero bajo supuestos explícitos |
| 6 | 9–15 nov | SHAP, errores, segmentos y ficha del modelo (model card) | Limitaciones documentadas |
| 7 | 16–22 nov | FastAPI, Streamlit, tests de API y Docker Compose | `docker compose up` funciona desde cero |
| 8 | 23–29 nov | Cambio de distribución simulado con Evidently, despliegue y README con resultados | URL pública y reproducibilidad verificadas |

**Prioridad:** la capa de decisión de la semana 5 es el entregable central. Si hay retrasos, se reduce primero el alcance del monitoreo de cambios de distribución de la semana 8.

Estado de cierre: semanas 1–2 verificadas, con la revisión de semana 2 pendiente; semanas 3–8 sin iniciar. La división se adelantó a semana 2 para reservar la prueba antes del EDA.

## Publicación y seguimiento

El repositorio está publicado en **https://github.com/darwinjaco/bank-churn-ml**, con `main` como rama predeterminada y `origin` configurado en la copia de trabajo.

El [workflow CI](https://github.com/darwinjaco/bank-churn-ml/actions/workflows/ci.yml) comprueba instalación con dependencias bloqueadas, lint, formato y tests con cobertura mínima del 85 %. Cada nueva publicación en `main` genera una ejecución. Las comprobaciones locales adicionales y la evidencia de cierre se mantienen en el registro de avance.

## Licencia

El código y la documentación están bajo [licencia MIT](LICENSE). El dataset está sujeto a las condiciones de su fuente original en Kaggle y se obtiene por separado.
