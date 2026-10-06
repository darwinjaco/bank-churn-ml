# Abandono bancario → Decisiones de retención

Proyecto de aprendizaje automático de extremo a extremo para estimar el abandono de clientes (**churn**) y **decidir a quién conviene contactar**, convirtiendo probabilidades calibradas en beneficio esperado bajo supuestos explícitos.

> En desarrollo. Semana 1 de 8: verificación local completada; publicación y CI remoto pendientes de crear el remoto. El detalle de cada sección está en el [registro de avance](docs/registro-avance.md).

## Objetivo de negocio

La pregunta central es: *con un presupuesto de retención, ¿a qué clientes debemos contactar y qué beneficio esperamos frente a no contactar a nadie, contactar a todos o seleccionar clientes al azar?*

El dataset no contiene ingresos del banco, valor de vida del cliente (CLV), costos de campaña ni resultados de intervenciones. Estas cantidades y la eficacia de la retención serán **supuestos documentados**, con análisis de sensibilidad. El beneficio será una estimación por escenarios, no un resultado económico observado ni una estimación causal.

## Estado actual

- Implementados: carga del CSV, contrato de datos con Pandera, reporte de calidad y tests.
- Configurados: uv, Ruff, pytest, pre-commit y GitHub Actions; cobertura mínima en CI del 85 %.
- Documentadas: especificaciones 001 y 002 en español.
- Verificados localmente: contrato del CSV, Ruff, formato, pre-commit y 22 tests; cobertura del 97,35 %.
- Reglas de trabajo: [AGENTS.md](AGENTS.md), incluidas especificación previa y exclusión permanente de `Gender` de las features.
- Repositorio público: [darwinjaco/bank-churn-ml](https://github.com/darwinjaco/bank-churn-ml), rama `main`. Publicación de los cambios de S02/S03 en curso.

La ejecución sin el CSV también pasó: 21 tests aprobados, 1 omitido y cobertura del 95,58 %, reproduciendo el escenario esperado del CI sin datos reales. Los resultados locales y el pendiente remoto están registrados en S02 y S03.

## Inicio rápido

Requisitos: Git y [uv](https://docs.astral.sh/uv/). La versión de referencia es Python 3.11, fijada en `.python-version`; el paquete admite Python `>=3.11,<3.13`.

Desde la raíz del proyecto, en PowerShell:

```powershell
uv sync --locked             # Crea .venv e instala las dependencias del archivo de bloqueo
uv run pre-commit install    # Instala las comprobaciones previas a cada commit
uv run pytest                # Usa datos sintéticos; omite el test real si falta el CSV
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

## Estructura del proyecto

```text
docs/         Registro de avance por fases y secciones
specs/        Especificaciones de diseño previas a la implementación
src/churn/    Paquete: configuración, carga y validación de datos
tests/        Tests con datos sintéticos y un test opcional con el CSV real
data/         raw/ y processed/; datos excluidos de Git
reports/      Reportes generados y evidencia de calidad
notebooks/    Exploración; la lógica reutilizable se implementará en src/churn/
```

## Especificaciones previstas

| N.º | Especificación | Estado |
|---|---|---|
| 001 | [Visión general y contrato de datos](specs/001-overview-and-data-contract.md) | Verificación local completada; cierre remoto pendiente |
| 002 | [Modelado y evaluación](specs/002-modeling-and-evaluation.md) | Documentada; implementación pendiente |
| 003 | Capa de decisión y beneficio esperado | Por redactar antes de la semana 5 |
| 004 | API y dashboard | Por redactar antes de la semana 7 |
| 005 | Operación: tests, Docker, CI y monitoreo | Por redactar antes de ampliar operación y serving |

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

## Preparación para GitHub

Una vez verificadas las comprobaciones locales y versionados los cambios que se publicarán:

1. Crea en GitHub un repositorio vacío llamado `bank-churn-ml`.
2. La rama local ya es `main`. Cuando esté creado el repositorio remoto y se indique publicar, configura su URL. Sustituye `TU_USUARIO` por tu usuario real:

   ```powershell
   git remote add origin https://github.com/TU_USUARIO/bank-churn-ml.git
   git push -u origin main
   ```

3. Comprueba la ejecución de GitHub Actions y registra su enlace como evidencia.
4. Añade al README los enlaces definitivos del repositorio y la insignia de CI.

## Licencia

El código y la documentación están bajo [licencia MIT](LICENSE). El dataset está sujeto a las condiciones de su fuente original en Kaggle y se obtiene por separado.
