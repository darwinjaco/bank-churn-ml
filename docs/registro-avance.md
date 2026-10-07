# Registro de avance

Documento de seguimiento del proyecto **Abandono bancario → Decisiones de retención**. Se actualiza al terminar cada sección de trabajo y enlaza la evidencia que permite cerrar una fase.

| Campo | Valor |
|---|---|
| Responsable | Darwin Jacome Cuenca |
| Inicio previsto | 5 de octubre de 2026 |
| Fin previsto | 29 de noviembre de 2026 |
| Dedicación estimada | 8 horas por semana; 64 horas en total |
| Última actualización | 7 de octubre de 2026 |
| Fase actual | Semana 8 publicada en `fd78f59` con CI remoto en verde; pendientes del responsable: Release `model-v1.0`, Docker con el Release, despliegue público (B-03), GIF y etiqueta `v1.0.0` |

Referencias: [README](../README.md), [especificación 001](../specs/001-overview-and-data-contract.md) y [especificación 002](../specs/002-modeling-and-evaluation.md).

## 1. Cómo usar este registro

- Una **fase** corresponde a una semana del cronograma; una **sección** es un bloque de trabajo con objetivo y alcance concretos.
- Estados: **pendiente**, **en curso**, **completada** o **bloqueada**. Una base implementada puede tener su cierre todavía pendiente.
- Al terminar una sección, registrar fecha, cambios, comprobaciones realmente ejecutadas, decisiones y siguiente paso.
- Marcar un criterio de cierre solo cuando su evidencia esté disponible. Diferenciar resultados históricos, comprobaciones locales y ejecuciones de CI.
- Si cambia el alcance o el calendario, conservar el plan inicial y anotar el ajuste en la sección correspondiente.

## 2. Seguimiento de fases

Todas las fechas corresponden a 2026 y representan objetivos de planificación.

| Fase | Fechas | Entregable | Criterio de cierre | Estado |
|---|---|---|---|---|
| Semana 1 | 5–11 oct | Repo, uv, Ruff, pytest, pre-commit, CI mínimo, specs 001–002 y Pandera | Tests pasan en CI | Completada el 6 de octubre: validación local y CI remoto verificados |
| Semana 2 | 12–18 oct | EDA, hipótesis y auditoría de productos 3–4 y balance cero | Hipótesis contrastadas con pruebas estadísticas, tamaños de efecto e incertidumbre | Completada y revisada el 6 de octubre; correcciones interpretativas incorporadas |
| Semana 3 | 19–25 oct | Pipeline, división estratificada, Dummy/LogReg y MLflow | Modelos de referencia registrados en MLflow | Completada y publicada (CI remoto en verde) |
| Semana 4 | 26 oct–1 nov | RF, XGBoost, validación cruzada y ajuste acotado | Tabla de media ± desviación estándar por modelo | Completada y publicada (`a868641..7013dfc`, CI #26); B-02 resuelto |
| Semana 5 | 2–8 nov | Calibración (E-04) y umbral monetario analítico (opción A); deciles y sensibilidad excluidos por decisión del responsable | Umbral justificado por beneficio esperado bajo supuestos explícitos | Completada |
| Semana 6 | 9–15 nov | SHAP, errores, segmentos, E-01, ficha del modelo y evaluación final (con confirmación) | Limitaciones documentadas | Completada |
| Semana 7 | 16–22 nov | FastAPI, Streamlit, tests de API y Docker Compose | `docker compose up` funciona desde cero | Implementada y publicada (CI remoto en verde); Docker verificado con modelo local; pendiente Release y Docker con Release |
| Semana 8 | 23–29 nov | Cambio de distribución simulado, despliegue y README final | URL pública y reproducibilidad verificadas | Implementada, verificada en local (S12) y publicada en `fd78f59` (CI en verde); despliegue pendiente (B-03) |

**Prioridad de alcance:** proteger la capa de decisión de la semana 5. Si hay retrasos, reducir primero el monitoreo de cambios de distribución de la semana 8 y registrar el ajuste.

## 3. Seguimiento de especificaciones

| Especificación | Tema | Estado | Momento previsto |
|---|---|---|---|
| 001 | Visión general y contrato de datos | Completada: verificación local y remota | Semana 1 |
| 002 | Modelado y evaluación | Completada v1.6: selección, calibración, auditoría y evaluación final en prueba (una vez) | Semanas 3–6 |
| 003 | [EDA e hipótesis preregistradas](../specs/003-eda-and-hypotheses.md) | Implementada v1.1 y revisada; H1–H6 congeladas en v1.0 | Semana 2 |
| 004 | Capa de decisión y beneficio esperado | Implementada v1.0 (opción A) | Semana 5 |
| 005 | API y dashboard | Implementada v1.1 (enmienda de la revisión de la semana 8); CI en verde (`fd78f59`); Docker con Release pendiente | Semana 7 |
| 006 | [Despliegue, monitoreo simulado y cierre](../specs/006-deployment-monitoring-release.md) | Implementada v1.0 y publicada (`fd78f59`, CI en verde); despliegue público pendiente (B-03) | Semana 8 |

## 4. Punto de partida — 6 de octubre de 2026

### Evidencia disponible al inicio (estado histórico)

- Commit inicial: `6037f9e` (`chore: week 1 scaffold, data contract and validation`).
- Repositorio local en `master`; el CI de push está configurado para `main` y no hay remoto de GitHub.
- Código de carga y validación implementado; herramientas y workflow configurados.
- CSV localizado en la carpeta de Descargas del usuario como `Churn_Modelling.csv`. La revisión del archivo muestra 10.000 registros y la cabecera esperada de 14 columnas, sin `Complain`.
- CSV pendiente de copia a `data/raw/` y validación completa en este entorno.
- [Reporte de calidad existente](../reports/data_quality.json): 20,37 % de abandono, 36,17 % de balances cero y 326 clientes con 3–4 productos.
- Resultados del contexto anterior: 22 tests, cobertura del 97 % y comprobaciones de Ruff/pre-commit satisfactorias. **Pendientes de reproducción local y de confirmación en CI.**

### Criterios de cierre de la semana 1 — estado tras S02/S03

- [x] Sincronizar el entorno con `uv sync --locked`.
- [x] Copiar el CSV a `data/raw/Churn_Modelling.csv` y ejecutar `churn-validate`.
- [x] Verificar tests, cobertura mínima del 85 %, Ruff y pre-commit.
- [x] Revisar cobertura de las infracciones del contrato; completar la evidencia de nulos, tipos y `RowNumber` con comprobaciones complementarias.
- [x] Versionar S01 con el mensaje solicitado y alinear la rama con `main`.
- [x] Crear `AGENTS.md` y alinear las especificaciones con sus reglas.
- [x] Crear el repositorio público y configurar el remoto con autorización del usuario.
- [x] Publicar con autorización del usuario y registrar una ejecución satisfactoria de CI.
- [x] Actualizar los criterios de aceptación con la evidencia local y remota obtenida.

## 5. Historial de secciones

### S01 — Documentación en español y revisión del diseño

| Campo | Valor |
|---|---|
| Fecha | 6 de octubre de 2026 |
| Fase | Semana 1 |
| Estado | Completada |
| Objetivo | Establecer documentación en español, coherente con el repositorio, y un registro de avance por fases |

**Trabajo realizado**

- Revisados README, ambas especificaciones, licencia, reporte, código, tests y configuración de herramientas/CI.
- Traducido el README con instrucciones de PowerShell, estado real, adquisición de datos, publicación y cronograma.
- Traducidas y ajustadas las especificaciones 001 y 002.
- Creado este registro para actualizarlo al cerrar cada sección.
- Identificadas las cinco especificaciones previstas y sus momentos de redacción.

**Archivos modificados o creados**

- `README.md`
- `specs/001-overview-and-data-contract.md`
- `specs/002-modeling-and-evaluation.md`
- `docs/registro-avance.md`

**Decisiones documentadas**

- Mantener `EstimatedSalary` como candidata hasta medir su contribución mediante E-03; su AUC individual no basta para excluirla.
- Tratar el posible origen sintético como hipótesis y limitar las conclusiones de la alarma univariada de fuga de información.
- Permitir seleccionar LogReg y exigir mejora frente a LogReg únicamente a candidatos más complejos.
- Ajustar calibradores con predicciones OOF de entrenamiento y evaluarlos en validación; reservar prueba para una evaluación final con decisiones congeladas.
- Conservar nombres de columnas, comandos e identificadores técnicos para mantener trazabilidad con el código.
- Mantener el texto legal de la licencia MIT original.

**Comprobaciones y evidencia**

- Revisión del estado inicial: árbol de trabajo limpio, rama `master` y sin remoto.
- `git diff --check`: satisfactorio, sin errores de espacios en los archivos modificados.
- `git diff --no-index --check -- /dev/null docs/registro-avance.md`: satisfactorio, sin errores de espacios en el documento nuevo.
- Revisión manual de enlaces relativos y del ancla `README.md#datos`: destinos existentes y referencias coherentes.
- Revisión de cifras contra `reports/data_quality.json` y consistencia entre README, especificaciones y cronograma: satisfactoria.
- Commit solicitado: `3104886` — `docs: translate specs/README, add progress log`. Incluye los cuatro archivos de S01; se eliminó la ruta absoluta del CSV antes de versionar.
- Antes de este commit se ejecutaron `uv sync --locked`, `uv run ruff check .`, `uv run ruff format --check .` y `uv run pytest --cov=churn --cov-report=term-missing --cov-fail-under=85`: 21 tests aprobados, 1 omitido por ausencia del CSV y cobertura del 95,58 %. Pre-commit se verificó posteriormente en S02.
- CI remoto no verificable al crear el commit por ausencia de remoto. La evidencia anterior es local, no una ejecución de GitHub Actions.

**Siguiente paso**

S01 versionada; la evidencia local de S02 y la remota de S03 respaldan el cierre de la semana 1.

### S02 — Entorno, CSV y verificación local

| Campo | Valor |
|---|---|
| Fecha | 6 de octubre de 2026 |
| Fase | Semana 1 |
| Estado | Completada: verificación local |
| Objetivo | Reproducir la validación y las comprobaciones de calidad con el entorno y CSV locales |

**Trabajo realizado**

- Copiado `Churn_Modelling.csv` desde Descargas a `data/raw/Churn_Modelling.csv` sin modificar el original.
- Instalado el entorno nuevo con Python 3.11.16 y las dependencias de `uv.lock`.
- Validado el CSV y regenerado `reports/data_quality.json`, sin diferencias respecto al reporte inicial.
- Ejecutados los comandos solicitados de Ruff, formato, pre-commit y pytest.
- Comprobado el rechazo de nulos en `Surname`, tipo incorrecto en `Age` y duplicados de `RowNumber`, complementando los tests existentes de rangos, categorías, `CustomerId` y columnas faltantes/adicionales.
- Confirmados cero valores nulos en el CSV y su exclusión de Git.
- Instalado el hook de pre-commit para futuros commits.

**Comandos ejecutados y salida resumida**

```text
Copy-Item -LiteralPath "$HOME\Downloads\Churn_Modelling.csv" -Destination "data/raw/Churn_Modelling.csv"
  Copia realizada; el CSV permanece excluido de Git.

uv sync --locked
  Resolved 36 packages. Entorno nuevo: Installed 34 packages.
  Segunda ejecución: Checked 34 packages; sin cambios en uv.lock.

uv run churn-validate --out reports/data_quality.json
  Código de salida 0; 10.000 filas y 0 duplicados.
  churn_rate=0.2037; balance_zero_share=0.3617.
  NumOfProducts=3: n=266, churn_rate=0.8271.
  NumOfProducts=4: n=60, churn_rate=1.0.
  low_salary_rows=59; surname_cardinality=2932.
  Cuatro advertencias informativas: balance cero, productos 3 y 4, salarios bajos.
  Sin alarma de fuga por AUC individual.

uv run ruff check .
  All checks passed!

uv run ruff format --check .
  12 files already formatted.

uv run pre-commit run --all-files
  8 hooks Passed; nbstripout Skipped (no files to check).

uv run pytest --cov=churn --cov-fail-under=85
  collected 22 items; 22 passed in 0.93s.
  TOTAL: 113 statements, 3 missed; Total coverage: 97.35%.
  Required test coverage of 85% reached.

uv run pre-commit install
  pre-commit installed at .git/hooks/pre-commit.

git check-ignore -v -- data/raw/Churn_Modelling.csv
  .gitignore:17:data/raw/*    data/raw/Churn_Modelling.csv
```

Comprobación complementaria con `uv run python -c`: `null_surname`, `wrong_age_dtype` y `duplicate_row_number` rechazados por Pandera; `raw null values: 0`. La primera invocación falló por escape de comillas en PowerShell (`SyntaxError`); se corrigió la invocación y la comprobación pasó, sin modificar código ni datos.

Verificación final después de actualizar la documentación:

- `uv run pre-commit run --all-files`: 8 hooks aprobados; `nbstripout` omitido por ausencia de notebooks.
- `uv run pre-commit run --files AGENTS.md`: comprobaciones pertinentes aprobadas; incluye explícitamente el archivo nuevo, todavía sin versionar.
- `git diff --check` y `git diff --no-index --check -- /dev/null AGENTS.md`: sin errores de espacios.
- Búsqueda documental: sin rutas absolutas del usuario ni referencias al antiguo experimento con `Gender` como entrada.
- `git diff -- reports/data_quality.json`: sin diferencias de contenido. `git ls-files --eol -- reports/data_quality.json` confirma LF en el índice y CRLF en la copia regenerada de Windows; por eso puede aparecer como modificado en el estado local.

**Decisiones y evidencia**

- Tests sin CSV antes de su copia: 21 aprobados, 1 omitido y 95,58 % de cobertura. Tests con CSV: 22 aprobados y 97,35 %; ambos superan el mínimo del 85 %.
- Se reproducen los resultados históricos de la semana 1. Los avisos de calidad motivan la auditoría de la semana 2; no son infracciones del contrato.
- Se creó `AGENTS.md` con las cinco reglas solicitadas. Se ajustó E-01 a auditoría por grupos: `Gender` nunca es feature, tampoco en experimentos.
- No se ha dividido el dataset ni evaluado un modelo sobre el conjunto de prueba; estas comprobaciones son de contrato y calidad de datos originales.
- Esta evidencia corresponde al entorno local de Windows; no acredita CI remoto en Linux.

**Archivos modificados o creados**

- `AGENTS.md`
- `README.md`
- `specs/001-overview-and-data-contract.md`
- `specs/002-modeling-and-evaluation.md`
- `docs/registro-avance.md`
- `data/raw/Churn_Modelling.csv` (solo local, excluido de Git).
- `reports/data_quality.json` regenerado, sin diferencias de contenido.

**Siguiente paso**

S03 completada tras la autorización de publicación y la verificación remota. Continuar con la semana 2.

### S03 — Preparación y publicación en GitHub

| Campo | Valor |
|---|---|
| Fecha | 6 de octubre de 2026 |
| Fase | Semana 1 |
| Estado | Completada: repositorio publicado y CI remoto verificado |
| Objetivo | Alinear rama y remoto, completar enlaces públicos y verificar CI |

**Trabajo realizado y comandos**

- Ejecutado `git branch -M main`: rama local renombrada correctamente, alineada con `.github/workflows/ci.yml`.
- Ejecutado `git remote -v`: sin salida; todavía no hay remoto configurado.
- Ejecutado `git log --oneline -2`: `3104886` (S01) y `6037f9e` (base de semana 1).
- Actualizado el README para reflejar la rama actual y los resultados locales.
- El usuario autorizó crear el repositorio y publicar para cerrar S03.
- `gh auth status`: cuenta activa `darwinjaco`, acceso a GitHub disponible.
- `gh repo create darwinjaco/bank-churn-ml --public --source . --remote origin --description "Predicción de abandono bancario y decisiones de retención basadas en beneficio esperado."`: repositorio creado y `origin` configurado.
- `git push -u origin main`: publicados los commits existentes hasta `3104886`; seguimiento de `origin/main` configurado.
- `gh run list --repo darwinjaco/bank-churn-ml --workflow ci.yml --branch main --commit 3104886e95677f170f06e86082bf913d702e2f0f --json databaseId,headSha,status,conclusion,url`: identificada la ejecución inicial.
- `gh run watch 37419338512 --repo darwinjaco/bank-churn-ml --exit-status --interval 10`: ejecución satisfactoria.
- `gh run view 37419338512 --repo darwinjaco/bank-churn-ml --log`: comprobados los resultados en Linux: 21 tests aprobados, 1 omitido y cobertura del 95,58 %.
- `gh repo view darwinjaco/bank-churn-ml --json url,visibility,defaultBranchRef`: repositorio público y rama predeterminada `main` confirmados.
- Antes del nuevo commit se ejecutaron `uv sync --locked`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run pre-commit run --all-files`, `uv run pre-commit run --files AGENTS.md` y `uv run pytest --cov=churn --cov-report=term-missing --cov-fail-under=85`: comprobaciones satisfactorias, 22 tests aprobados y cobertura local del 97,35 %.
- `git add` de los archivos previstos y `git diff --cached --check`: únicamente documentación y reglas versionadas; reporte normalizado en el índice sin diferencias de contenido. El CSV siguió excluido.
- `git commit -m "chore: verify week 1 and add agent rules"`: creado `3c157c0`; hooks del commit satisfactorios. Incluye `AGENTS.md`, README, registro y ambas especificaciones.
- `git push origin main`: publicado `3c157c0`.
- `gh run list` para el SHA completo de `3c157c0` y `gh run view 37419500890 --repo darwinjaco/bank-churn-ml --log`: CI del commit publicado satisfactorio, 21 tests aprobados, 1 omitido y cobertura del 95,58 %.
- Incorporados al README URL pública, instrucciones de clonación, insignia de CI y evidencia del cierre técnico. Marcada como completada la especificación 001.
- Para versionar el cierre documental se repitieron `uv sync --locked`, Ruff, formato, pre-commit y `uv run pytest --cov=churn --cov-report=term-missing --cov-fail-under=85`: todos satisfactorios; 22 tests aprobados y cobertura del 97,35 %. CI del commit previo `3c157c0` confirmado en verde antes del nuevo commit.

**Estado de publicación**

| Campo | Valor |
|---|---|
| Rama local | `main` |
| Commit de S01 | `3104886` — `docs: translate specs/README, add progress log` |
| Repositorio público | https://github.com/darwinjaco/bank-churn-ml |
| Remoto | `origin`: `https://github.com/darwinjaco/bank-churn-ml.git` |
| Push | Commits existentes y cambios de S02/S03 publicados con autorización del usuario |
| Commit publicado inicialmente | `3104886` |
| CI inicial | https://github.com/darwinjaco/bank-churn-ml/actions/runs/37419338512 |
| Commit de S02/S03 verificado | `3c157c0` — `chore: verify week 1 and add agent rules` |
| CI de cierre técnico | https://github.com/darwinjaco/bank-churn-ml/actions/runs/37419500890 |
| CI remoto en verde | Verificado para `3104886` y `3c157c0` |
| Resultado remoto | 21 tests aprobados, 1 omitido; cobertura del 95,58 % |

**Decisiones y cierre**

- Publicar primero los commits existentes permitió verificar CI remoto antes de crear nuevos commits, conforme a `AGENTS.md`.
- S01, S02 y S03 están completadas. El CSV está validado localmente y el código versionado pasa CI sin depender de datos reales.
- La primera ejecución remota confirma instalación, lint, formato y tests sin el CSV. Los hooks se ejecutan localmente como comprobación adicional.
- El cierre documental referencia la ejecución satisfactoria de `3c157c0`, que contiene las reglas y la evidencia de S02. La publicación del cierre documental generará además su propia ejecución de CI.
- Sin bloqueos pendientes de la semana 1. El siguiente trabajo requiere especificar la EDA y sus hipótesis antes de implementar.

**Siguiente paso**

Semana 2: definir la sección de EDA, hipótesis y protocolo estadístico en la especificación 001, preservando la reserva del conjunto de prueba, y después implementar la auditoría de calidad.

### S04 — T0: compuerta SDD de la semana 2

| Campo | Valor |
|---|---|
| Fecha | 6 de octubre de 2026 |
| Fase | Semana 2 |
| Estado | Completada |
| Objetivo | Versionar la especificación y el plan aprobados antes de modificar código, tests o dependencias |

**Trabajo realizado**

- Leídos `AGENTS.md`, `specs/003-eda-and-hypotheses.md` y `docs/plan-semana-2.md` antes de comenzar.
- Añadida `.gitattributes` con normalización LF para texto y PNG binarios.
- Añadidas las reglas 6 (compuerta SDD) y 7 (partición de prueba); la regla 2 permanece intacta.
- Renumeradas las especificaciones previstas: 003 EDA, 004 decisión, 005 serving y 006 operación.
- Actualizadas las referencias de la capa de decisión en la especificación 002; E-01 permanece intacta.
- Aprobadas la especificación 003 y el plan como v1.0, sin modificar H1–H6.
- La ejecución se adelanta al 6 de octubre por instrucción del usuario; se mantienen las fechas originales del cronograma.

**Comprobaciones y evidencia**

- Estado inicial: únicamente la especificación 003 y el plan nuevos, todavía sin versionar; sin otros cambios locales.
- CI previo en verde: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37419719367 (`9051f2e`).
- `git add --renormalize .`: ejecutado; sin cambios de contenido en código, tests ni reporte de calidad.
- `uv sync --locked`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run pre-commit run --all-files` y `uv run pytest --cov=churn --cov-fail-under=85`: satisfactorios; 22 tests aprobados y cobertura del 97,35 %.
- Los archivos nuevos de T0 quedaron incluidos en las comprobaciones de pre-commit.
- Commit T0: `678004d` — `docs: approve spec 003 and week 2 plan (SDD gate)`; publicado en `main` antes de modificar dependencias, código o tests.
- CI T0 en verde: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37421500954.

**Siguiente paso**

Compuerta satisfecha; continuar con T1 según el plan versionado.

#### Enmienda v1.1 — B-01 (6 de octubre de 2026)

- El responsable de diseño fijó Freeman–Halton por enumeración completa para tablas R×C con marginales fijos, con inclusión de probabilidades ≤ p_obs × (1 + 1e-7); para tablas 2×2 se mantiene Fisher bilateral exacto de scipy.
- Motivo: scipy utiliza remuestreo sin semilla en tablas distintas de 2×2. Se descarta Monte Carlo con semilla por ser aproximado y depender de la versión de scipy.
- Añadidos los dos valores de referencia aprobados a la especificación 003 §9. El procedimiento se implementará para tablas de dos columnas, como exige la resolución.
- Enmienda aplicada antes de T5 y de observar resultados reales de H1–H6. Las hipótesis, direcciones, umbrales y familia Holm permanecen congeladas desde v1.0.
- La frecuencia esperada aproximada de 53 en el grupo 3–4 es una previsión del responsable de diseño; no se ha ejecutado el contraste real. El fallback es una regla de robustez.
- Paso 1 solo documental, con mensaje `docs: amend spec 003 v1.1 (B-01 exact RxC test)`. Comprobaciones locales de `AGENTS.md` satisfactorias: 47 tests aprobados, 1 omitido y cobertura del 98,62 %. CI previo T3 en verde; pendiente la verificación remota de la enmienda tras publicar.
- La confirmación pendiente del CI de T3 se versionará en el paso 3 de la resolución, junto al cierre de B-01.
- Paso 1 publicado: `9e043df`. CI en verde: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37423573546. La primera cadena de comandos tuvo un error de sintaxis de PowerShell antes de ejecutar Git; se corrigió y se realizó un único commit.

### S05 — T1–T4: dependencias, división y contrastes

| Campo | Valor |
|---|---|
| Fase | Semana 2 |
| Estado | Completada: T1–T4 verificadas |
| Objetivo | Implementar exclusivamente la especificación 003 aprobada y el plan versionado |

| Tarea | Estado | Commit requerido |
|---|---|---|
| T1 | Completada | `build: add stats and EDA dependencies` |
| T2 | Completada | `feat: stratified split with versioned manifest` |
| T3 | Completada | `feat: statistical helpers with reference tests` |
| T4 | Completada | `feat: preregistered hypothesis tests H1-H6` |

#### T1 — Dependencias (6 de octubre de 2026)

- Añadidas a producción `scikit-learn`, `scipy` y `statsmodels`; creado el grupo `eda` con `matplotlib` e `ipykernel`.
- Ejecutados `uv add --no-sync scikit-learn scipy statsmodels`, `uv add --no-sync --group eda matplotlib ipykernel`, `uv lock` y `uv sync --locked --all-groups`.
- Resueltas 82 dependencias; instalación completa satisfactoria. Versiones estadísticas bloqueadas: scikit-learn 1.9.1, scipy 1.17.1 y statsmodels 0.15.0.
- Archivos: `pyproject.toml`, `uv.lock` y este registro. El CI sigue usando el grupo de producción y desarrollo: los tests actuales no necesitan gráficos.
- `uv sync --locked`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run pre-commit run --all-files` y `uv run pytest --cov=churn --cov-fail-under=85`: satisfactorios; 22 tests aprobados y cobertura del 97,35 % sin instalar el grupo `eda`.
- CI del commit previo T0 confirmado en verde antes del commit de T1. Pendiente: CI del nuevo commit tras la publicación.
- Commit T1: `e9cdb06`; publicado. CI satisfactorio: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37421692243.

#### T2 — División y manifiesto (6 de octubre de 2026)

- Implementados `make_split`, `build_manifest`, `load_exploration` y el CLI `churn-split` en `src/churn/split.py`.
- División según el protocolo: 20 % de prueba primero, después 75/25 del resto, estratificación por `Exited` y semilla 42.
- El manifiesto contiene tamaños, tasas, semilla, SHA-256 del CSV, hashes de los identificadores ordenados por partición y versión de scikit-learn.
- La exploración selecciona las filas permitidas al leer el CSV y excluye las columnas de auditoría; no hay lector de prueba.
- Tests de no solapamiento, cobertura de filas, tamaños, estratificación, determinismo, hashes, CLI y exclusión de clientes reservados. Un test con valores no convertibles en filas reservadas comprueba que el lector no las materializa.
- Comprobación focalizada: `uv run pytest tests/test_split.py --cov=churn --cov-report=term-missing`: 6 aprobados, 1 omitido; cobertura del módulo `split.py` del 100 %. El test real del manifiesto se activará al generar el artefacto en T5, según el orden del plan.
- `uv sync --locked`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run pre-commit run --all-files` y `uv run pytest --cov=churn --cov-fail-under=85`: satisfactorios; 28 tests aprobados, 1 omitido y cobertura global del 98,10 %.
- CI de T1 confirmado en verde antes del nuevo commit. Pendiente: CI de T2; la ejecución sobre el CSV real corresponde a T5.
- Commit T2: `ab73e70`; publicado. CI satisfactorio: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37422050721.

#### T3 — Funciones estadísticas (6 de octubre de 2026)

- Implementadas funciones puras en `src/churn/stats.py`: Wilson, diferencia de riesgo con Newcombe método 10, OR con IC Woolf, V de Cramér, Holm y AUC con IC bootstrap percentil.
- Añadidos `tests/test_stats.py` con referencias de la especificación y tolerancia `1e-4`, comprobaciones de n=0, tablas con ceros, determinismo del bootstrap y entradas que no permiten inferencia.
- Wilson, Newcombe, Woolf y Holm utilizan las implementaciones de statsmodels; Pearson usa scipy y AUC usa scikit-learn. No hay I/O en el módulo.
- Comprobación focalizada: `uv run pytest tests/test_stats.py`: 19 tests aprobados. Ruff detectó un signo menos Unicode ambiguo en un docstring; se cambió por el signo ASCII y las comprobaciones pasaron.
- `uv sync --locked`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run pre-commit run --all-files` y `uv run pytest --cov=churn --cov-fail-under=85`: satisfactorios; 47 tests aprobados, 1 omitido y cobertura global del 98,62 %. `stats.py` y `split.py` tienen cobertura del 100 %.
- CI previo T2 confirmado en verde. Pendiente: CI del commit T3 tras la publicación; no se avanza a T4 por B-01.
- Confirmación del CI de T3 versionada en el paso 3: `cd3350f` publicado, https://github.com/darwinjaco/bank-churn-ml/actions/runs/37422604079 satisfactorio; 46 tests aprobados, 2 omitidos y cobertura del 97,70 %.

#### Bloqueo B-01 — T4: Fisher para H2 con tabla 3×2

**Estado: resuelto el 6 de octubre de 2026.** El texto siguiente conserva el diagnóstico original; la resolución y su evidencia figuran después.

- La especificación 003 §4 exige Fisher si alguna frecuencia esperada es menor a 5, y H2 (§5) usa una tabla 3×2.
- El cálculo reproducible del p-valor de Fisher para esa tabla no está fijado: faltan el procedimiento y, si interviene remuestreo, su configuración.
- Diagnóstico exclusivamente sintético con scipy 1.17.1: dos llamadas a `fisher_exact([[8, 2], [1, 5], [0, 4]])` devolvieron p-valores `0.0093` y `0.0067`. Por tanto, usar el valor por defecto introduce remuestreo no preregistrado.
- Consultada la [documentación de scipy sobre Fisher](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.fisher_exact.html), que expone métodos de remuestreo para tablas distintas de 2×2.
- Según el rol de implementador y la regla 6, se detiene el avance a T4–T7. No se ha elegido un método, cambiado H1–H6 ni creado `hypotheses.py`.
- Para desbloquear: el responsable de diseño debe fijar el procedimiento para el caso 3×2 de H2 en una enmienda versionada de la especificación, con los parámetros necesarios para reproducirlo, antes de implementar T4.

#### Resolución B-01 — Paso 2 (6 de octubre de 2026)

- Implementados `freeman_halton(table)` e `independence_test(table)` en `stats.py`, después de versionar la enmienda v1.1.
- Enumeración completa, pesos combinatorios enteros y comparación exacta con la tolerancia aprobada; sin aleatoriedad ni aproximación Monte Carlo.
- Selector: Pearson sin Yates si todas las esperadas son ≥5, Fisher bilateral para 2×2 con esperadas pequeñas y Freeman–Halton para R×2.
- Tests de los dos valores de referencia (`1e-6`), determinismo, fila nula, invalidación de entradas y selección de las tres pruebas.
- `uv run pytest tests/test_stats.py`: 28 aprobados. Ruff señaló `zip` sin `strict`; corregido, lint y formato satisfactorios.
- Comprobaciones locales de `AGENTS.md` satisfactorias: 56 aprobados, 1 omitido, cobertura global del 98,79 % y `stats.py` al 100 %. CI previo de la enmienda confirmado en verde; pendiente el CI del commit `feat: exact Freeman-Halton test (B-01)` tras publicar.
- Paso 2 publicado: `4a3e4a6`. CI en verde: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37423861559.

#### Resolución B-01 — Paso 3: cierre documental

- Enmienda v1.1: `9e043df`; implementación exacta: `4a3e4a6`. Ambas publicadas y con CI satisfactorio.
- B-01 resuelto con el procedimiento definido por el responsable de diseño, sin alterar H1–H6 ni ejecutar T5 antes de la enmienda.
- Versionada en este paso la confirmación pendiente del CI de T3. Se mantiene un commit por tarea.
- Mensaje de este paso: `docs: close B-01 in progress log`. Siguiente tarea: T4 según la especificación v1.1.
- Comprobaciones locales completas de `AGENTS.md` satisfactorias: 56 aprobados, 1 omitido y cobertura del 98,79 %. CI del paso 2 en verde antes de este commit.
- Paso 3 publicado: `fc7ef62`. CI en verde: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37424012050.

#### T4 — Contrastes H1–H6 (6 de octubre de 2026)

- Implementada `HypothesisResult`, funciones H1–H6, selector exacto v1.1 en H1/H2/H5, Holm exclusivamente sobre H1–H5 y equivalencia para H6.
- H3 usa Logit con los tres términos fijados y H4 compara los modelos lineal y cuadrático mediante razón de verosimilitud. Los modelos son inferenciales del protocolo, no modelos predictivos de semana 3.
- Definiciones de saldo y tramos/centrado de edad en `config.py`; no se modificó la lista de features del modelo.
- CLI `churn-hypotheses` carga exclusivamente `load_exploration()` y serializa la prueba usada, efectos, IC, p-valores y veredictos.
- `uv run pytest tests/test_hypotheses.py --cov=churn --cov-report=term-missing`: 12 aprobados; incluye efectos sembrados, ausencia de efecto, coeficientes conocidos de H3/H4, selectores exactos, equivalencia, Holm y restricciones de módulos. Se corrigió el orden de imports señalado por Ruff.
- Sin contrastes sobre datos reales antes de T5. Comprobaciones completas de `AGENTS.md` satisfactorias: 68 aprobados, 1 omitido y cobertura del 98,76 %. CI del paso 3 confirmado en verde antes del commit; pendiente CI de T4.
- Commit T4: `f7e853e`; publicado. CI en verde: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37485327713.

### S06 — T5–T7: resultados, notebook y conclusiones

| Campo | Valor |
|---|---|
| Fase | Semana 2 |
| Estado | Completada y cerrada tras revisión |
| Objetivo | Generar los entregables de EDA y detenerse para revisión al terminar T7 |

| Tarea | Estado | Commit requerido |
|---|---|---|
| T5 | Completada | `chore: generate split manifest, hypothesis results and figures` |
| T6 | Completada | `docs: EDA notebook` |
| T7 | Completada; revisión interpretativa incorporada | `docs: week 2 conclusions and log` |

#### T5 — Resultados y figuras (6 de octubre de 2026)

- Ejecutados `uv run churn-split`, `uv run churn-hypotheses` y `uv run --group eda python -m churn.plots`, después de la enmienda v1.1 y de T4.
- División real: 6.000 / 2.000 / 2.000; tasas 0,203833 / 0,2035 / 0,2035. Exploración: 8.000 filas; el manifiesto registra hashes y versión, y los índices permanecen fuera de Git.
- H1–H6 cumplen los criterios preregistrados. H1 DR 0,122732; H2 V 0,387502; H3 OR ajustado 2,178704; H4 coeficiente -0,003429 y pico 56,58 años; H5 DR -0,106183; H6 AUC 0,514582 con IC [0,499739; 0,530557]. Los p-valores Holm corresponden solo a H1–H5.
- Seis PNG generados: productos (H2, agrupación 3–4), edad, OR de Alemania, balance con masa cero, salario y actividad. Tamaños: 17.190, 17.701, 18.214, 21.522, 16.503 y 15.831 bytes; todos <200.000 bytes.
- `plots.py` no contiene inferencia: dibuja IC y efectos del JSON y distribuciones descriptivas. No se excluye de cobertura: se prueba con Matplotlib headless y los tamaños reales de PNG.
- `uv run pytest tests/test_plots.py`: 2 aprobados. Se retiraron comentarios `noqa` innecesarios detectados por Ruff.
- El CI pasa a `uv sync --locked --all-groups` porque los nuevos tests gráficos necesitan el grupo `eda`; no se añadieron dependencias adicionales.
- Comprobaciones locales de `AGENTS.md` y sincronización adicional `uv sync --locked --all-groups` satisfactorias: 71 tests aprobados, incluido `realdata` del manifiesto; cobertura global del 98,48 %, sin exclusiones de cobertura.
- `git check-ignore -v -- data/processed/split.json data/raw/Churn_Modelling.csv`: ambos excluidos. CI de T4 en verde antes del commit; pendiente CI de T5 tras publicar.
- Commit T5: `c937861`; publicado. CI en verde: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37486403134.

#### T6 — Notebook (6 de octubre de 2026)

- Creado `notebooks/01_eda.ipynb`, con cuatro celdas de código: carga de exploración, tipos/cardinalidades/distribuciones, reporte JSON y figuras ya generadas.
- Sin funciones, lambdas, inferencia o modelos propios; único lector de filas: `load_exploration()`.
- `uv run ruff format notebooks/01_eda.ipynb`, `uv run ruff check notebooks/01_eda.ipynb` y `uv run pre-commit run nbstripout --files notebooks/01_eda.ipynb`: satisfactorios tras ordenar los imports.
- Validación con `uv run --group eda python -c`: ejecutadas las cuatro celdas, AST sin definiciones de funciones y carga de 8.000 filas únicamente de entrenamiento/validación. Confirmados `outputs=[]` y `execution_count=null` en el archivo.
- Comprobaciones locales completas de `AGENTS.md`, con instalación adicional del grupo EDA, satisfactorias: 71 aprobados y cobertura del 98,48 %; `nbstripout` incluido y aprobado. CI de T5 en verde antes del commit; pendiente CI de T6 tras publicar.
- Commit T6: `0585806`; publicado. CI en verde: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37487169164; 69 aprobados, 2 omitidos por ausencia del CSV y cobertura del 98,05 %.

#### T7 — Conclusiones y cierre (6 de octubre de 2026)

- Creado `reports/eda_hypotheses.md`: tabla H1–H6 con efectos, IC, Holm, prueba usada y veredicto; una conclusión por hipótesis, sin lenguaje causal.
- Secundarios Mann–Whitney y KS en sección **Exploratorio**, sin veredictos confirmatorios. H6 no tiene p Holm; H2 presenta IC Wilson por nivel, no un IC inexistente de V.
- Implicaciones limitadas a las candidatas y auditorías ya previstas (`has_balance`, `age_band`, E-02 y E-03); no se cambió la selección de features ni se implementó semana 3.
- Añadidos Q-06–Q-11 a la especificación 001, con muestra de 8.000 filas explícita. README actualizado con resultados, reproducción, grupo EDA y renumeración de specs 003–006.
- Criterios de la especificación 003 contrastados con artefactos y tests; H1–H6 y reglas de equidad/prueba permanecen intactas.
- Evidencia técnica remota antes del cierre documental: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37487169164, correspondiente a `0585806`. Este commit documental tendrá además su propia ejecución de CI al publicarse.
- Comprobaciones finales completas de `AGENTS.md`, con sincronización adicional de EDA, satisfactorias: 71 tests aprobados y cobertura del 98,48 %; Ruff, formato y todos los hooks pertinentes, incluido `nbstripout`, aprobados. CI de T6 confirmado en verde antes del commit `docs: week 2 conclusions and log`.
- Commit T7: `4c786ae`; publicado. CI en verde: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37488588746; 69 aprobados, 2 omitidos y cobertura del 98,05 %.

#### Revisión interpretativa y cierre de S06 (6 de octubre de 2026)

- Calculados los segmentos exclusivamente mediante `load_exploration()`, en 8.000 filas de entrenamiento y validación. El código reproducible está incluido y citado en `reports/eda_hypotheses.md`, sección **Exploratorio**.
- `uv run python -c` para el cálculo y para ejecutar literalmente el bloque Python del reporte: Alemania con saldo cero 0/2.005; Alemania con saldo positivo 663/2.005 (33,0673 %); Francia + España con saldo cero 393/2.891 (13,5939 %) y con saldo positivo 574/3.104 (18,4923 %); DR estratificada −4,8983559001 pp. Cifras y denominadores verificados.
- Aclarado el soporte común de H3 en saldo positivo y la confusión parcial de H5 con `Geography`. Se conserva el veredicto preregistrado de H5 y se interpreta la DR estratificada como asociación descriptiva, no atribución causal.
- Ampliado Q-10 existente, sin duplicar identificadores: ausencia de saldo cero en Alemania, posible artefacto y señal compartida. Manejo indicado por la revisión: SHAP de `has_balance` y `Geography` en conjunto y evitar interpretar sus coeficientes por separado en semana 3.
- P-valores <1e-10 representados como «< 10⁻¹⁰» únicamente en la tabla legible. No se modificaron `src/`, los JSON de resultados/manifiesto ni los veredictos.
- S06 cerrada con esta revisión; semana 3 no iniciada. Mensaje del commit solicitado: `docs: week 2 review corrections`.
- `uv sync --locked`, sincronización adicional `uv sync --locked --all-groups`, Ruff, formato, pre-commit y `uv run pytest --cov=churn --cov-report=term-missing --cov-fail-under=85`: satisfactorios; 71 tests aprobados y cobertura del 98,48 %. Ruff solicitó compactar una línea del bloque Python del reporte; corregido antes del commit.
- `git diff --exit-code -- src tests pyproject.toml uv.lock reports/hypotheses.json reports/split_manifest.json`: sin diferencias, confirmando que código, dependencias, JSON y veredictos no cambiaron.
- CI previo T7 confirmado en verde: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37488588746. La publicación de esta revisión documental generará su propia ejecución de CI, que se verificará antes de dar por terminada la tarea.

**Cierre de S04–S06 y compuertas**

- S04 completada: spec y plan tuvieron commit antes de código; la enmienda exacta v1.1 precedió a los resultados reales.
- S05 completada: división reproducible, funciones estadísticas, pruebas exactas y contrastes preregistrados con tests de referencias y efectos conocidos.
- S06 completada y revisada: artefactos, notebook y conclusiones verificados, con evidencia local y remota; correcciones de soporte y composición geográfica incorporadas. Los análisis secundarios quedan separados y sin lenguaje causal.
- B-01 resuelto. Sin bloqueos pendientes de semana 2; revisión interpretativa cerrada según las correcciones del responsable de diseño.
- Semana 3 pendiente de nuevas instrucciones. No comenzar entrenamiento ni selección de variables en esta sección documental.

### S07 — Semana 3: pipeline, baselines y MLflow

| Campo | Valor |
|---|---|
| Fecha de apertura | 6 de octubre de 2026 |
| Fechas planificadas | 19–25 de octubre de 2026 |
| Estado | Completada y publicada (CI remoto en verde; ver S08) |
| Objetivo | Tres baselines fijas con CV exclusivamente de entrenamiento, transformaciones seguras y trazabilidad MLflow |

| Tarea | Estado | Commit requerido |
|---|---|---|
| T0 | Completada | `docs: amend spec 002 v1.1 and week 3 plan (SDD gate)` |
| T1 | Completada | `fix: figure readability (week 2 debt)` |
| T2 | Completada | `build: add mlflow` |
| T3 | Completada | `feat: leakage-safe feature transformers` |
| T4 | Completada | `feat: model pipelines for baselines` |
| T5 | Completada | `feat: cross-validation harness with MLflow tracking` |
| T6 | Completada | `chore: baseline results` |
| T7 | Lectura y cierre verificados; revisión pendiente | `docs: week 3 results and log` |

#### T0 — Enmienda y compuerta SDD

- Leídos AGENTS, especificación 002 y estado del repositorio antes de implementar. Árbol limpio y CI de `b83caba` en verde: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37496270556.
- Creado el plan completo autorizado de T0–T7. Se mantienen las fechas previstas; ejecución anticipada por instrucción del usuario.
- Enmienda 002 v1.1: FS-RAW/FS-EDA, categorías de productos no monótonas, edad escalada/cuadrática dentro de pliegues, reglas R1–R5, baselines fijas, cuatro métricas con ddof=1 y trazabilidad MLflow.
- Motivo: H2 desaconseja la codificación ordinal para LogReg informada; H4 requiere no linealidad, y usar `config.centered_age()` fuera de sklearn produciría fuga de las medias del pliegue. Q-10 fija la interpretación conjunta de saldo y geografía.
- Solo documentación hasta el commit de T0. Sin selección de modelo, acceso a prueba ni uso de validación para entrenamiento.
- Ejecutadas las comprobaciones de `AGENTS.md`, incluida sincronización adicional `uv sync --locked --all-groups`: 71 aprobados y cobertura del 98,48 %; Ruff, formato y hooks satisfactorios. CI previo confirmado en verde. Pendientes: commit de compuerta y CI de T0.
- Compuerta publicada: `566a07b`; CI en verde: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37508772980, antes de cambios en `src/`, tests o dependencias de semana 3.

#### T1 — Presentación de figuras

- `plots.py`: miles en ejes numéricos, `constrained_layout=True` para los dos paneles de saldo, color único de barras/puntos, IDs H1–H6 y tasas con `PercentFormatter`.
- Alemania: umbral práctico OR=1,5 con etiqueta y figura más compacta; se conserva la referencia OR=1.
- `uv run --group eda python -m churn.plots`: seis PNG regenerados, de 17.094 a 26.795 bytes; todos <200 KB.
- Revisadas visualmente las seis imágenes: sin solapamientos de títulos, etiquetas o paneles. Datos, intervalos, histograma y resultados confirmatorios sin cambios (`git diff --exit-code` de hypotheses.json y split_manifest.json satisfactorio).
- Comprobaciones completas de `AGENTS.md`, con instalación adicional de EDA, satisfactorias: 71 aprobados y cobertura del 98,51 %. CI previo T0 en verde; pendiente CI de T1 tras publicar.
- Commit T1: `a8b8506`; CI en verde: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37509243601.

#### T2 — MLflow

- `uv add --no-sync mlflow`, `uv lock` y `uv sync --locked --all-groups`: satisfactorios; MLflow completo 3.16.1, con 144 paquetes resueltos.
- Archivos modificados: `pyproject.toml`, `uv.lock` y registro. Se conserva el tracking temporal en los tests que se implementarán en T5.
- Comprobaciones locales de `AGENTS.md`, con EDA adicional, satisfactorias: 71 aprobados y cobertura del 98,51 %. CI previo T1 en verde. Pendiente CI de T2; si el tamaño impide CI, se registrará el bloqueo sin sustituir la dependencia.
- Commit T2: `83b1e69`; CI en verde: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37509729792. La dependencia completa no bloqueó CI.

#### T3 — Transformadores

- `features.py`: `HasBalance` y `ProductsGroup` sin estado y con nombres de salida; fábrica de edad con `StandardScaler` seguido de `PolynomialFeatures` de grado 2 sin bias.
- `FEATURE_SETS` contiene solo las nueve entradas originales permitidas; las derivadas se generan en el pipeline. Constantes de umbral y clip fijadas en config.
- `uv run pytest tests/test_features.py`: seis aprobados, incluida la prueba A→B que conserva la media de A y prohíbe usar `config.centered_age()`.
- Ruff pidió nombres de argumentos en minúscula; corregidos sin omitir reglas. Comprobaciones completas satisfactorias: 77 aprobados, cobertura global del 98,61 % y `features.py` al 100 %. CI previo T2 en verde; pendiente CI de T3 tras publicar.
- Commit T3: `1888bc9`; CI en verde: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37510509610.

#### T4 — Pipelines

- `build_pipeline` combina defensa de auditoría, ColumnTransformer y Dummy/LogReg con la configuración fija aprobada. FS-EDA agrupa productos antes de one-hot y ajusta escala/cuadrática de edad dentro del pipeline.
- Se rechaza explícitamente un DataFrame con columnas de auditoría, también al predecir; categorías desconocidas producen error. Nombres de salida sin IDs ni auditoría.
- `uv run pytest tests/test_pipeline.py --cov=churn --cov-report=term-missing`: siete aprobados y módulo pipeline al 100 %.
- Scikit-learn 1.9.1 avisa que el argumento `penalty` se deprecará; la configuración L2 aprobada es válida en la versión bloqueada y se conserva, sin suprimir advertencias ni cambiar hiperparámetros.
- Comprobaciones completas satisfactorias: 84 aprobados y cobertura del 98,72 %; cuatro advertencias de deprecación documentadas. CI previo T3 en verde; pendiente CI de T4 tras publicar.
- Commit T4: `8d31299`; CI en verde: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37511264883.

#### T5 — CV y MLflow

- `load_training()` filtra inmediatamente entrenamiento; CV clona el pipeline en cada uno de los cinco pliegues fijos. Métricas AP, ROC-AUC, Brier y log loss, media y desviación muestral ddof=1.
- Se registran hashes de índices de ajuste/puntuación por pliegue para verificar que los modelos usan las mismas particiones, sin publicar CustomerId.
- MLflow: experimento `bank-churn`, URI de entorno o SQLite local aprobado, hiperparámetros, métricas agregadas y por step, y todas las etiquetas exigidas. CLI `churn-baselines` ejecuta únicamente las tres configuraciones aprobadas.
- Tests con URI SQLite temporal y directorio de trabajo `tmp_path`; no se creó `mlruns/` en el proyecto. Incluyen prevalencia/ROC de Dummy, determinismo, mismos pliegues, exclusión de IDs de validación/prueba y campos/historiales de MLflow.
- `uv run pytest tests/test_train.py --cov=churn --cov-report=term-missing`: seis aprobados, módulo train al 97 %. Advertencias de deprecación de sklearn/SQLAlchemy observadas, sin suprimirlas ni alterar configuraciones.
- Comprobaciones completas satisfactorias: 90 aprobados y cobertura del 98,56 %; 25 advertencias de bibliotecas documentadas. CI previo T4 en verde; pendiente CI de T5. Todavía no se han ejecutado baselines reales.
- Commit T5: `c75af93`; CI en verde: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37512680458.

#### T6 — Ejecución real

- `uv run churn-baselines`: tres corridas de CV sobre 6.000 filas de entrenamiento; cinco pliegues fijos, sin métricas de validación externa o prueba.
- `reports/baselines.json`: métricas de cada pliegue, resumen, parámetros, procedencia y run IDs. `reports/baselines.md`: tabla generada desde el JSON, con código reproducible de formateo.
- AP media ± std: Dummy 0,203833 ± 0,000456; LogReg-RAW 0,459104 ± 0,029316; LogReg-EDA 0,656790 ± 0,028053. Sin selección de modelo.
- Verificación con `uv run python -c`: tres corridas FINISHED en `sqlite:///mlruns/mlflow.db`, experimento `bank-churn`; todas las medias/std de MLflow coinciden con JSON y la tabla MD coincide con su generador.
- Réplica de CV sin registrar nuevas corridas: métricas e índices exactamente iguales para las tres configuraciones. Se conservan solo tres corridas reales en el tracking.
- Run IDs: Dummy `67f346cabc794a749c709d298a8a77d8`, RAW `22b313957b96480bbd21f50a4130b1df`, EDA `bef5ae63e7b8421abcfee5f1ad65dd5c`. Código registrado: `c75af93fbfb0dd87f51efeb39fa70071caa4d399`; etiquetas `final=false`.
- Comprobaciones completas satisfactorias: 90 aprobados y cobertura del 98,56 %. Base MLflow, CSV e índices excluidos de Git verificados con `git check-ignore`. CI previo T5 en verde; pendiente CI de T6 tras publicar.
- Commit T6: `8e8b309`; CI en verde: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37514109690. Resultado remoto: 88 aprobados, 2 omitidos por ausencia del CSV y cobertura del 98,24 %.

#### T7 — Lectura descriptiva y cierre

- `reports/baselines.md`: cuatro líneas descriptivas, sin elegir modelo ni lenguaje causal. Diferencia de AP EDA−RAW calculada desde JSON: 0,1976860408, mayor que std RAW 0,0293164275 y EDA 0,0280529011; no se presenta como prueba estadística.
- README: tabla completa de las tres baselines, FS-RAW/FS-EDA, reproducción y ubicación MLflow, hoja de ruta y espera de revisión. La selección/calibración de fases posteriores siguen pendientes.
- Ubicación local de las corridas: `mlruns/mlflow.db`, experimento `bank-churn`; run IDs consignados en T6 y `reports/baselines.md`. Los tests usan `tmp_path`, no ese tracking real.
- Evidencia remota del código y resultados publicados antes del cierre documental: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37514109690. El commit de cierre documental tendrá su propia ejecución de CI tras publicar.
- Comprobaciones finales completas de `AGENTS.md`, con EDA adicional, satisfactorias: 90 aprobados y cobertura del 98,56 %. Ruff, formato y todos los hooks pertinentes en verde. CI previo T6 en verde antes del commit `docs: week 3 results and log`; la publicación documental tendrá su propia ejecución posterior.

**Cierre de S07 y alcance**

- Compuerta SDD respetada: `566a07b` antecede a cambios de código y dependencias; todos los mensajes de T0–T6 corresponden al plan aprobado.
- Tres configuraciones fijas, mismos cinco pliegues exclusivamente de entrenamiento, métricas y trazabilidad completas; ninguna transformación aprendida usa `config.centered_age()` fuera de sklearn.
- Rechazo explícito de auditoría en el pipeline, IDs excluidos, sin remuestreo ni ponderación y sin usar validación externa o prueba para métricas.
- S07 cerrada técnicamente, sin bloqueos pendientes. No se elige modelo ni se avanza a semana 4; la revisión del responsable de diseño es el siguiente paso.

### S08 — Semana 4: árboles, ajuste, selección y ablaciones

| Campo | Valor |
|---|---|
| Fecha de apertura | 6 de octubre de 2026 |
| Fechas planificadas | 26 de octubre–1 de noviembre de 2026 |
| Estado | Completada y publicada (`a868641..7013dfc`, CI #26 en verde); B-02 resuelto |
| Objetivo | Fijar el protocolo antes de entrenar, comparar familias en FASE B y ejecutar E-03/E-02 sin consultar prueba |

| Tarea | Estado | Commit requerido |
|---|---|---|
| T0 | Completada | `docs: amend spec 002 v1.2 and week 4 plan (SDD gate)` |
| T1 | Completada (`53d909a`; CI tras push) | `fix: baseline report precision and paired differences` |
| T2 | Completada (`bd4962c`; CI tras push) | `build: add xgboost` |
| T3 | Completada (`14b3e01`; CI tras push) | `feat: tree pipelines and preregistered search spaces` |
| T4 | Completada (`365185e`; CI tras push) | `feat: two-phase tuning and re-evaluation` |
| T5 | Completada (`bb5e4d0`; CI tras push) | `feat: preregistered model selection rule` |
| T6 | Completada (`e0b5c7b` código, `cfca063` resultados) | `feat: model selection and ablation experiments` |
| T7 | Completada; publicada (`7013dfc`, CI #26 en verde) | `docs: week 4 model selection and experiments` |

#### T0 — Enmienda v1.2 y observaciones de semana 3

- Leídos AGENTS, spec 002, reporte y código existentes. Estado inicial limpio; CI de `98aae24` en verde: https://github.com/darwinjaco/bank-churn-ml/actions/runs/37515966324.
- Creado el plan completo T0–T7 y actualizado Estado/Versión de la spec, FS-TREE, espacios y presupuestos, FASE A/B, orden de ejecución, uso único de validación y decisiones de E-03/E-02.
- Motivo de la enmienda: separar búsqueda optimista de reevaluación, congelar presupuestos y comparaciones antes de entrenar y fijar parsimonia de salario frente a la auditoría de productos. La regla de selección §6 pasos 1–5 y E-01 permanecen intactas.
- O3 aplicada. O1/O2 se difieren a T1, conforme a la condición del plan: el generador existente es un bloque Python embebido en el Markdown; implementar funciones de reporte y sus tests requiere cambios de código posteriores a esta compuerta. El JSON de baselines permanece intacto.
- Cálculo de O2 mediante `uv run python -c` desde `baselines.json`, comprobando hashes de pliegues: Δ AP [0,178426436; 0,230043639; 0,193189012; 0,192766200; 0,194004916], media 0,197686041, std ddof=1 0,019208887 y 5/5 positivos. A tres decimales: +0,198 ± 0,019.
- No se han modificado `src/`, tests ni dependencias, ni ejecutado entrenamiento, ajuste, selección o ablaciones de semana 4. Ejecución anticipada por instrucción del usuario; se mantienen las fechas planificadas.
- Comprobaciones completas de `AGENTS.md`, con sincronización adicional EDA, satisfactorias: 90 aprobados y cobertura del 98,56 %; Ruff, formato y hooks en verde. Sin diferencias en `src/`, tests, dependencias o reportes de baselines. CI previo verificado en verde; pendientes commit y CI de T0. La continuación requiere resolver B-02 antes de implementar o entrenar.
- Confirmación de T0 versionada en T1: `860393c`, CI satisfactorio https://github.com/darwinjaco/bank-churn-ml/actions/runs/37524372835.

#### Bloqueo B-02 — Agregación de OOF repetidas para E-02

**Estado: resuelto por la decisión del responsable de diseño; enmienda v1.3 pendiente de commit.** Se conserva a continuación el diagnóstico original.

- §5.1 fija `RepeatedStratifiedKFold` con dos repeticiones: cada cliente obtiene dos predicciones OOF. §7 pide AP excluyendo el grupo 3–4 y probabilidad media predicha de ese grupo, pero no define el tratamiento de las dos predicciones por cliente.
- Elegir agregación de probabilidades por cliente, acumulación de las predicciones de ambas repeticiones o cálculo separado por repetición cambia la AP reportada. No es solo una decisión de formato.
- Diagnóstico sintético, sin entrenar ni consultar datos reales de semana 4: y=[0,1,0,1], predicciones de repetición 1=[0,1;0,9;0,7;0,6] y repetición 2=[0,8;0,7;0,2;0,5]. AP tras media de probabilidades por cliente=1; AP agrupando ambas repeticiones=0,691667; media de AP por repetición=0,708333.
- En cumplimiento del rol de implementador y la compuerta SDD, se detiene la continuación. No se ha elegido un procedimiento ni modificado la regla de selección o los criterios de E-03.
- Para desbloquear, el responsable de diseño debe fijar en una enmienda versionada cómo se construyen las probabilidades OOF para E-02 (b)/(c) y cómo se cuenta n cuando hay dos repeticiones. El protocolo debe quedar definido antes de los resultados reales.

#### Enmienda v1.3 — resolución de B-02

- Decisión recibida: calcular E-02 (b)/(c) por repetición, reportando ambos valores y su media; no promediar probabilidades ni duplicar clientes al juntar repeticiones. n cuenta clientes únicos del segmento.
- Comparador de E-02 (b): AP de todos los clientes calculada por repetición, no media por pliegue. OOF con CustomerId, repeat 0/1, fold, y y proba.
- Referencia incorporada a §9: AP 0,833333 y 0,583333, media 0,708333. §6 y E-03 permanecen sin cambios.
- La confirmación pendiente del CI de T0 se versionará junto con T1, según instrucción del usuario. Esta enmienda es solo documental y precede a todo código de semana 4.
- Comprobaciones completas de `AGENTS.md`, con EDA adicional, satisfactorias: 90 aprobados, cobertura del 98,56 %, lint/formato/hooks en verde. CI previo T0 confirmado en verde; pendiente CI de la enmienda tras el commit `docs: amend spec 002 v1.3 (B-02 OOF aggregation per repetition)`.
- Enmienda publicada: `a868641`, CI en verde https://github.com/darwinjaco/bank-churn-ml/actions/runs/37526758149. B-02 cerrado antes de código o resultados reales.

#### T1 — Precisión y diferencias pareadas

- Nuevo `reports.py`: tablas a tres decimales, diferencias pareadas con validación de pliegues y std ddof=1; regeneración reproducible de `baselines.md` con `uv run python -m churn.reports`.
- O1/O2 implementadas sin modificar `baselines.json`; AP pareada +0,198 ± 0,019, con cinco signos positivos. Se conserva trazabilidad de las corridas históricas.
- `uv run pytest tests/test_reports.py`: dos aprobados; cálculo desde JSON sintético, signos positivo/negativo/cero, pliegues incompatibles y render/CLI verificados.
- Corregidos signos Unicode ambiguos y longitud de cadenas señalados por Ruff, sin omitir reglas. Comprobaciones completas satisfactorias: 92 aprobados, cobertura del 98,49 %, hooks/lint/formato en verde. CI previo de v1.3 en verde; pendiente CI de T1 tras publicar.
- Cambio de rol a petición del responsable: desde T1, Claude implementa T1–T7 además de planificar. Entorno Linux aislado (`UV_PROJECT_ENVIRONMENT` fuera del repo, sin tocar `.venv` de Windows). Los hooks de `pre-commit` no pueden descargarse desde GitHub en ese entorno; se ejecutan sus equivalentes de PyPI (`pre-commit-hooks==5.0.0`, `nbstripout==0.8.1`) con los mismos argumentos. Commits locales; el push y el CI quedan a cargo del responsable. El hook instalado en `.git/hooks/pre-commit` apunta al intérprete de Windows y no es ejecutable desde Linux; por eso los commits de Claude usan `core.hooksPath` vacío tras ejecutar los hooks equivalentes y quedan validados por CI al publicar.
- Verificación de T1 por Claude: Ruff y formato en verde; hooks equivalentes en verde; 92 aprobados, cobertura 98,49 %.

#### T2 — Dependencia XGBoost

- Se usa `xgboost-cpu>=3.2` (misma API `import xgboost`) en lugar de `xgboost`: en Linux, `xgboost` arrastra `nvidia-nccl-cu12` (cientos de MB) sin aportar nada en CPU. `uv.lock` sin paquetes NVIDIA y con ruedas para Windows y Linux.
- Verificación: `import xgboost` → 3.2.0; Ruff, formato, hooks equivalentes y pytest en verde.

#### T3 — Pipelines de árboles y espacios preregistrados

- `build_pipeline(model, feature_set, exclude=(), params=None)`: `rf`/`xgb` solo con FS-TREE (valores sin escalar, `NumOfProducts` entero, `has_balance`, Geography one-hot); `exclude` admite únicamente `EstimatedSalary` y `NumOfProducts` (E-03/E-02); `params` fija hiperparámetros del clasificador. El `InputGuard` se mantiene.
- `search_spaces.py`: copia literal de §4 y §5.1 (presupuestos 20/40/40, semillas 42 y 2027, 5×2 pliegues).
- R3 verificado por test: RF `class_weight=None`; XGBoost `scale_pos_weight=1`, `hist`, `logloss`, sin early stopping.
- Tests nuevos: espacios idénticos a la spec, rechazo de `Gender`, ausencia de escalado, determinismo de RF/XGBoost, ablaciones y combinaciones inválidas. 105 aprobados, cobertura 98,59 %.
- Aviso no bloqueante: scikit-learn 1.9 marca `penalty="l2"` como obsoleto (se elimina en 1.10). Se conserva porque la spec lo fija; migrar a `l1_ratio=0` requerirá enmienda.

#### T4 — Ajuste en dos fases

- `tune.py`: `tune_family` (FASE A, `RandomizedSearchCV` con `StratifiedKFold(5, shuffle=True, 42)`, AP, `refit=False`, semilla 42; puntaje marcado como optimista) y `reevaluate` (FASE B, `RepeatedStratifiedKFold(5, 2, 2027)`, idéntica para todas las familias). OOF con `CustomerId`, `repeat`, `fold`, `y`, `proba` en `data/processed/oof_phaseB.parquet` (fuera de Git). CLI `churn-tune` → `reports/tuning.json`.
- `tracking.py`: procedencia (commit, hash del CSV y del manifiesto) y registro genérico en MLflow con `stage ∈ {tuning, reevaluation}`.
- Corrección de robustez sin efecto en resultados: el one-hot de `NumOfProducts` en FS-EDA usa categorías fijas {1, 2, 3} (R2) en vez de aprenderlas en cada pliegue; con pliegues sin clientes 3–4 fallaba. Baseline `logreg-eda` reproducida: diferencia máxima por métrica 1,1·10⁻¹⁶ (redondeo de coma flotante).
- Tests: pliegues de FASE B idénticos entre llamadas y distintos de FASE A; cada cliente una vez por repetición; parámetros fijos y muestreados presentes; registro MLflow en URI temporal; CLI con salida JSON y parquet. 113 aprobados, cobertura 98,19 %.

#### T5 — Regla de selección

- `selection.py`: `select_candidate` (pasos 1–2 con AP media y std de FASE B; cercano = diferencia < std del mejor o media igual; orden LogReg > RF > XGBoost) y `validate_choice` (pasos 3–5; "superar" = AP estrictamente mayor). Funciones puras, sin E/S.
- Tests por rama: candidato claramente mejor, cercanos → el más simple, frontera estricta (diferencia = std no es cercano), medias iguales, fallo frente a Dummy, complejo que supera a LogReg, LogReg conservada, empates en validación y rama LogReg.
- Observación: la salida `criterio_fallido` del paso 4 es lógicamente inalcanzable (si el candidato supera a Dummy y LogReg ≥ candidato, LogReg supera a Dummy). Se mantiene por fidelidad literal a §6 y se excluye de cobertura.
- Desde T5, el cómputo pesado se ejecuta en el entorno en la nube de Claude: los procesos en segundo plano no sobreviven en el entorno enlazado y la búsqueda supera el límite por llamada. Se usa un clon exacto (bundle de Git del mismo commit), el mismo CSV (SHA-256 `3996cd1f…`), el mismo `uv.lock` y una copia de `mlruns/mlflow.db`, que se devuelve al repositorio con las nuevas corridas.

#### Aclaración v1.4 de la spec 002 (antes de resultados de E-02)

- La v1.3 no fijaba si las OOF de E-02 (b)/(c) correspondían a la configuración con salario (FASE B original) o a la final tras E-03. Se fija la configuración final, porque E-02 audita el modelo que se desplegará y §6 ordena E-02 después de E-03. También se explicita que Dummy usa FS-RAW en validación.
- Se versiona antes de ejecutar `churn-select` sobre datos reales; la búsqueda de FASE A/B (`churn-tune`) no depende de esta aclaración.

#### T6 — Código de selección y experimentos

- `experiments.py`: orden fijo de §6 (pasos 1–2 con FASE B → E-03 → E-02 sobre la configuración final → ajuste con todo el entrenamiento → validación, pasos 3–5). `load_validation()` es la primera lectura de validación; no existe cargador de prueba. CLI `churn-select` → `reports/model_selection.json`; corridas MLflow `stage=experiment` (E-02, E-03) y `stage=selection`.
- Funciones puras con tests: Δ pareada por (repetición, pliegue); umbral E-03 inclusivo en −0,005; AP por repetición con la referencia B-02 (0,833333; 0,583333; media 0,708333); segmentos de E-02 con error si un cliente se repite dentro de una repetición.
- Comprobaciones con `pre-commit` real (disponible en el entorno en la nube): todos los hooks en verde; 130 aprobados, cobertura 98 %.
- El código se versiona antes de la ejecución real para que la procedencia de las corridas apunte a este commit; los resultados van en un commit aparte.

#### T6–T7 — Resultados reales y cierre

- `uv run churn-tune` (≈8 min, 2 núcleos) y `uv run churn-select`, en un clon exacto del commit `e0b5c7b`. FASE B: LogReg 0.655 ± 0.027; RF 0.686 ± 0.018; XGBoost 0.697 ± 0.018. Puntajes de búsqueda (optimistas) entre 0,002 y 0,007 por encima.
- §6: mejor XGBoost; RF cercano (diferencia 0.011 < std 0.018) → **RF** por parsimonia. Validación (primer uso, una vez): Dummy 0.203, RF 0.696, LogReg 0.637 → `complejo_supera_logreg`; modelo final RF sin `EstimatedSalary`.
- E-03: Δ AP +0.0033 ± 0.0040 (8/10 positivos) ≥ −0,005 → se elimina el salario.
- E-02: (a) Δ AP sin productos -0.113 ± 0.021 (10/10 negativos); (b) AP todos 0.687 frente a 0.608 sin el grupo 3–4 (n = 5,799); (c) grupo 3–4 (n = 201): observado 87.1%, predicho 73.2%.
- **Verificación independiente** (script sin importar `churn`, solo pandas/scikit-learn): RF FASE B con salario 0,6864 ± 0,0181, sin salario 0,6897 ± 0,0179; Δ E-03 +0,0033 ± 0,0040 con 8/10 positivos; AP de validación RF sin salario 0,6964 y Dummy 0,2035. Coinciden con los JSON.
- Reportes: `reports/model_selection.md` generado desde los JSON (`python -m churn.selection_report`), con test que compara cifras. README con tabla de la semana 4 y tabla de la semana 3 a tres decimales. Spec 002 §8: dos criterios marcados.
- Comprobaciones con `pre-commit` real: hooks en verde; suite completa en verde con cobertura ≥ 98 %.

**Hallazgos para la semana 5**

- E-02 (c): el modelo subestima el riesgo del grupo 3–4 en ~14 pp. Debe considerarse en la calibración (E-04) y en la ficha del modelo.
- La procedencia `split_manifest_sha256` se calcula sobre los bytes del archivo y depende del final de línea: copia CRLF de Windows `978161d4…` (semana 3) frente a LF de Git `4354b7e0…` (semana 4). El contenido es idéntico. Propuesta para la T0 de la semana 5: calcular el hash sobre el JSON canónico o tras normalizar a LF.
- scikit-learn 1.9 advierte que `penalty="l2"` se eliminará en 1.10; migrar a `l1_ratio=0` requiere enmienda.
- La salida `criterio_fallido` del paso 4 de §6 es inalcanzable por construcción (documentado en T5).

### S09 — Semana 5: calibración y capa de decisión

| Campo | Valor |
|---|---|
| Fecha de apertura | 6 de octubre de 2026 |
| Fechas planificadas | 2–8 de noviembre de 2026 |
| Estado | Completada y publicada (`7013dfc..fbae9cc`, CI #27 en verde) |
| Objetivo | Calibrar el Random Forest final (E-04), aplicar el umbral analítico de la spec 004 y congelar el artefacto, sin consultar prueba |

| Tarea | Estado | Commit requerido |
|---|---|---|
| T0 | Completada (`895f293`) | `docs: spec 004 decision layer, spec 002 v1.5 and week 5 plan (SDD gate)` |
| T1 | Completada (`8bfd342`) | `fix: canonical split manifest hash` |
| T2 | Completada (`cc74f95`) | `feat: probability calibration (E-04)` |
| T3 | Completada (`fa7472e`) | `feat: expected-profit decision layer (spec 004)` |
| T4 | Completada (`f2796d5`) | `feat: calibrate, decide and freeze artifact` |
| T5 | Completada (`364fe26`) | `chore: calibration and decision results` |
| T6 | Completada; publicada (`fbae9cc`, CI #27 en verde) | `docs: week 5 calibration and decision` |

#### T0 — Compuerta

- Semana 4 publicada: `a868641..7013dfc`, CI #26 en verde. Copia temporal de Claude eliminada.
- Decisión del responsable: **solo opción A** (umbral analítico c/(s·V) = 1/6 con V = 1.000 €, c = 50 €, s = 30 %). Opciones B (presupuesto/deciles) y C (umbral robusto/sensibilidad) excluidas y registradas como trabajo futuro; el cronograma de la semana 5 se ajusta en consecuencia.
- Spec 004 v1.0 redactada; spec 002 v1.5 fija el detalle de E-04 (OOF 5 pliegues semilla 42, sigmoide `LogisticRegression(C=np.inf)`, isotónica, empate de Brier < 1e-4), el artefacto y el hash canónico del manifiesto (hallazgo de la semana 4). Todo antes de calibrar.

#### T1 — Hash canónico del manifiesto

- `tracking.manifest_sha256()`: SHA-256 de `json.dumps(contenido, sort_keys=True, separators=(",", ":"))`; lo usan `tracking.provenance()` y `train.main()`. Valor actual: `09ee6a9697dc…`. Los hashes históricos sobre bytes de las semanas 3 (`978161d4…`, CRLF) y 4 (`4354b7e0…`, LF) corresponden al mismo contenido.
- Tests: mismo hash con LF, CRLF y claves reordenadas; hash distinto si cambia el contenido; `provenance()` usa el hash canónico.

#### T2 — Calibración (E-04)

- `calibration.py`: `oof_predictions` (5 pliegues, semilla 42, `clone` por pliegue), calibradores `none`/`sigmoid` (`LogisticRegression(C=np.inf)` sobre p)/`isotonic` (`IsotonicRegression` acotada y recortada), `choose_calibrator` (menor Brier; empate < 1e-4 resuelto sin calibrar > sigmoide > isotónica), `reliability_table` (10 cuantiles), `group_calibration` y `CalibratedModel` (pipeline + calibrador para el artefacto).
- Tests con una puntuación sintética que subestima el riesgo (score = p²): ambas calibraciones bajan el Brier en datos no vistos, salidas en [0, 1], sigmoide monótona, isotónica recorta fuera de rango; reglas de empate; OOF completa y determinista. Sin advertencias con `-W error`.

#### T3 — Capa de decisión

- Supuestos en `config.py` (V = 1.000 €, c = 50 €, s = 0,30, política aleatoria 20 %). `decision.py`: `threshold()` = c/(s·V) = 1/6, `decide()` con desigualdad estricta (en t* exacto, EB = 0, no se contacta), `realized_benefit()` y `evaluate_policies()` (nadie, todos, aleatoria 20 % como valor esperado analítico, modelo, oráculo), con métricas y matriz de confusión en t*.
- Tests con valores calculados a mano: t* = 1/6; EB = [−50, 0, 10, 250]; caso de 10 clientes con beneficio de cada política, diferencia frente a la mejor referencia, fracción del oráculo y matriz de confusión.

#### T4 — Orquestación y artefacto

- `decide.py` y CLI `churn-decide`: lee la configuración final de `model_selection.json` (RF, FS-TREE sin `EstimatedSalary`), genera OOF de entrenamiento, ajusta los calibradores, ajusta el pipeline con todo el entrenamiento, compara variantes en validación, elige por Brier y aplica la regla de la spec 004 con la probabilidad calibrada elegida.
- Artefacto en `models/` (fuera de Git): `model.joblib` (`CalibratedModel`: pipeline + calibrador + columnas) y `metadata.json` (variables, exclusiones, hiperparámetros, calibrador, umbral, supuestos, versiones, procedencia; evaluación final "pendiente"). Copia de la metadata en `reports/model_metadata.json`. Figura `reports/figures/reliability.png`. MLflow `stage=calibration` (etiqueta `experiment=E-04`) y `stage=decision`.
- Tests de extremo a extremo con datos sintéticos: el artefacto recargado reproduce el número de contactados del reporte; metadata idéntica en ambas copias.

#### T5 — Resultados reales y verificación independiente

- `uv run churn-decide` (≈14 s) en el entorno enlazado, con el código de `f2796d5`; corridas añadidas a `mlruns/mlflow.db` (copia previa conservada fuera del repositorio).
- E-04 en validación: Brier sin calibrar 0,1026, **sigmoide 0,1010**, isotónica 0,1013 → sigmoide (diferencia > 1e-4). La sigmoide conserva la AP (0,696); la isotónica la reduce a 0,673 por empates. Grupo 3–4 de validación (n = 56): observado 80,4 %; predicho sin calibrar 73,4 %, con sigmoide 84,1 %.
- Decisión (t* = 1/6, 2.000 clientes, 407 abandonos): el modelo contacta a 621 (31,1 %), captura 310 abandonos y obtiene **61.950 €**; contactar a todos 22.100 €; aleatoria 20 % 4.420 €; nadie 0 €; oráculo 101.750 €. Diferencia frente a la mejor referencia: +39.850 €; 60,9 % del oráculo. Precisión 0,499; recall 0,762; F1 0,603.
- Verificación independiente (script sin importar `churn`): Brier 0,1026 / 0,1010 / 0,1013; 621 contactados, 310 capturados, 61.950 €, 22.100 € y 101.750 €. Coincide con `decision.json`.
- Figura de fiabilidad revisada: sin calibrar subestima el decil de mayor riesgo (≈71 % predicho frente a ≈82 % observado); la sigmoide lo corrige.

#### T6 — Reporte y cierre

- `decision_report.py` genera `reports/decision.md` desde `decision.json` (test que compara cifras y salida de la CLI). README con la sección de la semana 5; spec 002 §8 (selección/calibración y artefacto marcados; E-01 pendiente) y spec 004 §9 completos.
- Pendiente para la semana 6: E-01 (auditoría por `Gender`), SHAP agrupando `has_balance` y `Geography` (R4), análisis de errores y segmentos, y ficha del modelo con el sesgo del grupo 3–4 y los límites de la spec 004. La evaluación final en prueba sigue reservada.

#### Verificación previa a la semana 6

- Sincronización: `main` local = `origin/main` = `fbae9cc`; árbol limpio. CI #27 en verde (1 min 23 s).
- **Clon limpio desde GitHub** (entorno Linux independiente, `uv sync --locked --all-groups`, mismo CSV): `churn-split` regenera el manifiesto sin cambios; `churn-validate` reproduce `data_quality.json`; 148 tests aprobados **sin omitidos** (incluidos los de datos reales), cobertura 98,31 %.
- **Reproducción completa del pipeline** en ese clon (`churn-hypotheses` → `churn-baselines` → `churn-tune` → `churn-select` → `churn-decide`, ≈ 8 min): `hypotheses`, `baselines`, `tuning`, `model_selection` y `decision` idénticos a los versionados (tolerancia 1e-9), salvo procedencia (run IDs, commit, hash del manifiesto). En `model_metadata` solo cambia la versión de parche de Python (3.11.16 frente a 3.11.15).
- Artefacto `models/model.joblib` recargado sobre validación: 621 contactados con p > 1/6, igual que `decision.json`; columnas sin `Gender`; metadata idéntica a su copia en `reports/`.
- Controles estáticos: ningún módulo carga la partición de prueba; `Gender` solo aparece como columna de auditoría; spec 003 marcada como implementada.
- Observación: `.python-version` fija solo 3.11 (no el parche); no afecta a los resultados.

### S10 — Semana 6: explicabilidad, auditoría y ficha del modelo

| Campo | Valor |
|---|---|
| Fecha de apertura | 7 de octubre de 2026 |
| Fechas planificadas | 9–15 de noviembre de 2026 |
| Estado | Completada y publicada (CI #29 en verde) |
| Objetivo | Explicar el modelo congelado, auditar errores, segmentos y género (E-01) en validación, redactar la ficha y, con confirmación, hacer la única evaluación en prueba |

| Tarea | Estado | Commit requerido |
|---|---|---|
| T0 | Completada (`2659ef1`) | `docs: spec 002 v1.6 and week 6 plan (SDD gate)` |
| T1 | Completada (`928bea6`) | `build: add shap` |
| T2 | Completada (`a28f6aa`) | `feat: SHAP explanations with grouped features` |
| T3 | Completada (`2ee7455`) | `feat: error, segment and E-01 fairness audit` |
| T4 | Completada (`6e398a3` código, `97b4aed` resultados) | `chore: explainability and audit results` |
| T5 | Completada (`0b82172`) | `docs: week 6 audit and model card` |
| T6 | Completada (`764cb00` código, `6e8e54d` resultados; CI #29 en verde) | `feat: final test evaluation` |

#### T0 — Compuerta

- Semana 5 y verificación publicadas (`a99517f`). Spec 002 v1.6 §11 fija, antes de calcular: SHAP con aditividad y agrupación R4; errores en t*; segmentos; E-01 con bootstrap (2.000 réplicas, semilla 42) y señal de alerta (IC sin 0 y |Δ| ≥ 0,05); ficha del modelo; evaluación final única con confirmación explícita.
- `AGENTS.md` regla 7: excepción única `load_test_once` para §11.6.
- Prueba técnica previa de compatibilidad (sin versionar): `shap` 0.51 con `numba` 0.68 funciona con el lock actual; 200 filas en 2,9 s.

#### T1–T2 — SHAP

- `shap>=0.51` añadido (sin paquetes NVIDIA en el lock).
- `explain.py`: `compute_shap` (TreeExplainer sobre el RF base, clase 1, probabilidad sin calibrar) que **falla si la aditividad no se cumple** (tolerancia 1e-6); `global_importance` (media |SHAP| por variable y por grupo, sumando SHAP por fila dentro del grupo: Geography, saldo y saldo + geografía según R4); `local_explanations` (mayor p, más cercano a t* por encima, menor p; cinco contribuciones de mayor magnitud).
- Tests con un modelo pequeño: aditividad, orden, agrupaciones, ausencia de `Gender`, selección correcta de los tres clientes y caso sin clientes sobre el umbral.

#### T3 — Auditoría

- `audit.py`: segmentos de §11.3 (`productos` en {1, 2, 3-4}; `Gender` solo para auditar), métricas por segmento (n, tasa observada, p media, brecha de calibración, tasa de contacto, sensibilidad, precisión, abandonos no contactados, beneficio), segmento con mayor proporción de abandonos no contactados, perfiles VP/FP/FN/VN, banda ±0,05 alrededor de t* y E-01 con bootstrap estratificado por género (2.000 réplicas, semilla 42) y la señal de alerta preregistrada.
- Tests: caso de valores conocidos, denominadores vacíos, regla de alerta en sus cuatro casos, bootstrap determinista que detecta una brecha sembrada y no la marca cuando no existe.

#### T4 — Orquestación (código)

- `run_audit.py` y CLI `churn-audit`: carga el artefacto congelado, añade `Gender` a validación solo para auditar (unión por `CustomerId`; el modelo selecciona sus columnas y nunca recibe `Gender`), calcula SHAP, errores, segmentos y E-01, comprueba que el artefacto reproduce los contactados de `decision.json` (si no, falla) y registra en MLflow (`stage=audit`, `experiment=E-01`). Figura `reports/figures/shap_importance.png`.
- Corrección: los perfiles de error devuelven `None` en grupos vacíos en lugar de fallar.
- El código se versiona antes de la ejecución real.

#### T4 — Resultados reales y verificación independiente

- `uv run churn-audit` (≈37 s) con el artefacto de la semana 5: 621 contactados (igual que `decision.json`); aditividad SHAP con error máximo 9·10⁻¹⁵.
- **SHAP global:** Age 0,103 > NumOfProducts 0,071 > IsActiveMember 0,054 > Geography=Germany 0,027 > Balance 0,015 > has_balance 0,013; grupo saldo + geografía (R4) 0,054. Coherente con H1–H4.
- **Errores en t*:** los FN son más jóvenes (37 frente a 47 años en VP), más activos y con más saldo cero: abandonos "silenciosos". Mayor proporción de abandonos no contactados: tramo 18–29 (65,4 %, solo 26 abandonos). Banda ±0,05 alrededor de t*: 319 clientes, abandono 20,4 %.
- **Segmentos:** brechas de calibración entre −2,3 y +3,8 pp; el grupo 3–4 (n = 56) se contacta al 100 % con 80 % de abandono.
- **E-01 (Gender):** tasa de contacto 31,2 % frente a 31,0 % (Δ +0,002, IC [−0,039; 0,044]); sensibilidad 77,5 % frente a 74,7 % (Δ +0,027, IC [−0,057; 0,109]); brecha de calibración −1,8 frente a +1,9 pp (Δ −0,038, IC [−0,067; −0,009], |Δ| < 0,05: sin alerta); **precisión 59,6 % frente a 42,2 % (Δ +0,174, IC [0,103; 0,252]): alerta preregistrada.** Las tasas base difieren (24,0 % frente a 17,5 %), por lo que con igual tasa de contacto la precisión es mayor en mujeres; además, al excluir `Gender` el modelo subestima levemente a las mujeres y sobrestima a los hombres. Solo se reporta, según §11.4.
- Verificación independiente (sin importar `churn`): métricas por género, ranking SHAP y segmento 18–29 idénticos.
- Figura `shap_importance.png` revisada.

#### T5 — Reportes y ficha del modelo

- `model_card.py` genera `reports/audit.md` (SHAP global y local, perfiles de error, segmentos, E-01 con IC y lectura) y `reports/model_card.md` (resumen, uso previsto y no previsto, datos, variables, selección, calibración y decisión, explicabilidad y equidad, limitaciones, evaluación final "pendiente" y trazabilidad), ambos desde los JSON; test que compara cifras y salida de la CLI. README con la sección de la semana 6.
- Siguiente: T6, la única evaluación en prueba (§11.6), solo con confirmación explícita del responsable.

#### T6 — Evaluación final en prueba (código)

- **Confirmación explícita del responsable** recibida el 7 de octubre de 2026 para ejecutar la única evaluación en prueba.
- `final_eval.py` y CLI `churn-final`: comprueba primero la metadata (`final_test_evaluation = "pendiente"`) y el umbral; `load_test_once` se niega si existe `reports/final_test.json` y verifica el SHA-256 de los `CustomerId` de prueba y su tamaño contra el manifiesto versionado. Evalúa el artefacto congelado (AP, ROC-AUC, Brier, log loss y políticas de la spec 004), registra en MLflow `stage=final`, `final=true` y marca la metadata como completada. La ficha incorpora la sección de prueba si existe el JSON.
- Tests: verificación del manifiesto, rechazo de una segunda ejecución (por archivo y por metadata) y actualización de ambas copias de la metadata.

#### T6 — Resultado de la evaluación final (única)

- `uv run churn-final` el 2026-10-07 con el artefacto `f2796d5`: verificación del manifiesto superada; MLflow `stage=final`, `final=true` (`9e57e27ccaad44cf99a03471d3b99092`).
- Prueba (2.000 clientes, abandono 20.35%): AP 0.7047, ROC-AUC 0.8616, Brier 0.1017, log loss 0.3380; probabilidad media 0.2050 (bien calibrada).
- Decisión en t*: contacta a 634, captura 311 de 407 abandonos, beneficio 61,600 € frente a 22,100 € (todos) y 101,750 € (oráculo); 60.5% del oráculo. Precisión 0.491, sensibilidad 0.764.
- Coherente con desarrollo (validación: AP 0,696, Brier 0,1010, 61.950 €; FASE B: AP 0,690 sin salario): sin señales de sobreajuste a la validación.
- Verificación independiente (script sin `churn`, reproduce la misma evaluación sin tomar decisiones): AP 0,7047, ROC-AUC 0,8616, Brier 0,1017, 634 contactados, 311 capturados, 61.600 €. Coincide.
- Metadata marcada como completada; una segunda ejecución falla por diseño. Spec 002 §8: todos los criterios cumplidos. Ficha del modelo con la sección de prueba.

### S11 — Semana 7: API, dashboard y Docker

| Campo | Valor |
|---|---|
| Fecha de apertura | 7 de octubre de 2026 |
| Fechas planificadas | 16–22 de noviembre de 2026 |
| Estado | T0–T7 implementadas; Docker verificado en Windows con el modelo local; pendiente: Release `model-v1.0` (CI en verde desde `30c0809`) |
| Objetivo | Servir el modelo congelado con FastAPI y Streamlit, reproducible con `docker compose up`, sin CSV ni reentrenamiento |

| Tarea | Estado | Commit requerido |
|---|---|---|
| T0 | Completada (`ce0abeb`) | `docs: spec 005 api and dashboard, week 7 plan (SDD gate)` |
| T1 | Completada (`80ab9d0`) | `build: add serving dependencies` |
| T2 | Completada (`0e473a1`) | `feat: model artifact download with hash check` |
| T3 | Completada (`8d96805`) | `feat: FastAPI service` |
| T4 | Completada (`ae3e9e0`) | `feat: optional LLM explanation with template fallback` |
| T5 | Completada (`11867df`) | `feat: Streamlit dashboard` |
| T6 | Completada (`36babc9`); verificada en Docker Desktop (`3a741c6`, `1b300a2`) | `build: docker image and compose` |
| T7 | Completada (`5b391f9`) | `docs: week 7 api, dashboard and docker` |

#### T0 — Compuerta

- Decisiones del responsable: artefacto por **GitHub Release** con verificación SHA-256 (`579b7fe3…`), despliegue en **Hugging Face Spaces (Docker)** y **LLM opcional** con interfaz compatible con OpenAI (NVIDIA NIM u OpenRouter), desactivado sin clave y con plantilla determinista.
- Spec 005 v1.0: endpoints `/health`, `/model`, `/predict`, `/predict/batch`, `/explain`; contrato Pydantic con campos extra prohibidos (`Gender` → 422); dashboard que solo consume la API; tests y criterios de aceptación.

#### T1–T2 — Dependencias y artefacto

- Dependencias: `fastapi`, `uvicorn`, `streamlit`, `openai` (cliente compatible para el LLM opcional) y `httpx` (dev, para `TestClient`). Sin paquetes NVIDIA en el lock.
- `artifact.py`: URL del Release `model-v1.0`, SHA-256 `579b7fe3…095a`; `ensure_model()` descarga a un archivo temporal, verifica y solo entonces lo mueve; falla si el hash no coincide (también para archivos ya presentes); `load_model()` carga solo tras verificar; `MODEL_PATH` y `MODEL_URL` configurables. Tests sin red con descargador simulado, y comprobación de que el hash publicado coincide con el artefacto local.

#### T3 — API

- `api.py`: `Customer` (Pydantic, `extra="forbid"`, rangos del contrato; `EstimatedSalary` opcional e ignorada), `Batch` (1–1.000), `Service` (modelo, metadata, SHA-256 y evaluación final cargados una vez en el `lifespan`), endpoints `/health`, `/model`, `/predict` (probabilidad calibrada, contacto, beneficio esperado, umbral y 3 razones SHAP con dirección) y `/predict/batch` (resumen de contactados y beneficio esperado). Umbral y supuestos desde la metadata.
- Tests (14) con modelo sintético: equivalencia exacta con `predict_proba`, regla y beneficio, salario ignorado, 422 por rango, categoría, `Gender`, `CustomerId` o campo faltante, límites del lote y carga del servicio.
- Prueba de humo con el artefacto real: `/health` devuelve el SHA-256 publicado y `/predict` responde con la evaluación final disponible en `/model`.

#### T4 — Explicación opcional con LLM

- `narrative.py`: cliente compatible con OpenAI configurado solo por `LLM_BASE_URL`, `LLM_API_KEY` y `LLM_MODEL` (por ejemplo, NVIDIA NIM `https://integrate.api.nvidia.com/v1` u OpenRouter `https://openrouter.ai/api/v1`); tiempo de espera 10 s y sin reintentos. Solo envía las ocho variables del contrato, la probabilidad, la decisión, el beneficio, el umbral y las razones; nunca identificadores ni `Gender`. Sin configuración, con error o con respuesta vacía, devuelve una plantilla determinista. Endpoint `POST /explain`.
- Tests: plantilla sin clave, respuesta del LLM simulada, ausencia de `CustomerId`, `Surname` y `Gender` en lo enviado, caída por tiempo de espera y respuesta vacía, y `/explain` con 422 para `Gender`.

#### T5 — Dashboard

- `ui.py` (sin Streamlit, testeado): cliente HTTP (`API_URL`, por defecto `http://localhost:8000`), `prepare_batch` (solo columnas del contrato: descarta `Gender`, identificadores y salario; 1–1.000 filas), `results_table`, `reason_rows` y formato en euros.
- `dashboard/app.py`: pestañas Cliente (formulario → probabilidad, decisión, beneficio, razones SHAP y texto con su origen), Lote (CSV → resumen, tabla ordenada y descarga) y Modelo (regla, supuestos y evaluación final). No carga el modelo: todo pasa por la API.
- Prueba de humo con `streamlit.testing.AppTest` y la API real levantada con `uvicorn`: sin excepciones; cliente de 52 años, inactivo, de Alemania → 90,4 %, contactar, 221 €, razones Age, IsActiveMember y Geography=Germany; pestaña Modelo con AP 0,705 y 61.600 €.

#### T6 — Docker

- `Dockerfile` (una imagen: `python:3.11-slim`, `uv` 0.12.13, dependencias con `--locked --no-dev`, usuario 1000 para Spaces, sin CSV): copia código, dashboard, `model_metadata.json` y `final_test.json`; descarga el modelo del Release y **el build falla si el SHA-256 no coincide** (`ARG MODEL_URL`). `docker/start.sh` con `ROLE=api|dashboard|all` (en `all`, la API escucha en 127.0.0.1:8000 y Streamlit en 7860 con XSRF desactivado para el iframe de Spaces). `docker-compose.yml` con dos servicios (API 8000 con *healthcheck*, dashboard 8501 que espera a la API) y variables LLM opcionales. `.dockerignore` y `.env.example`.
- `artifact.py`: permisos 0644 al guardar el modelo (el temporal nace con 0600).
- **Limitación del entorno de verificación:** el proxy de Claude bloquea Docker Hub, GHCR, ECR y MCR, así que no pudo ejecutarse `docker build` (ni `docker build --check`, que también resuelve la imagen base). Verificaciones hechas: `docker compose config` válido; `shellcheck` sin avisos; **réplica exacta de los pasos de la imagen** en un directorio limpio (mismos archivos copiados, `uv sync --locked --no-dev`, descarga del modelo por HTTP con verificación del hash y `ROLE=all bash docker/start.sh`): `/health` con el SHA-256 publicado, `/predict` 0,947 y contactar, `Gender` → 422, `/explain` con plantilla y Streamlit `/_stcore/health` = ok.
- Pendiente: `docker compose up --build` real (equipo del responsable o build de Hugging Face en la semana 8), que requiere publicar antes el Release `model-v1.0`.

#### T7 — Documentación

- README con endpoints, ejecución con y sin Docker, LLM opcional y pasos para publicar el Release `model-v1.0`. Spec 005: tres criterios marcados; quedan `docker compose up` y CI.
- **Acciones del responsable:** (1) publicar el Release con `models/model.joblib`; (2) `docker compose up --build` y abrir `http://localhost:8501`; (3) push y revisión del CI.

#### Verificación Docker en Windows (6 de octubre de 2026)

- Docker Desktop 29.8.2. Como el Release aún no existe, se añadió la variante `MODEL_SOURCE=local` (`docker-compose.local.yml`, `verify-docker.ps1 -LocalModel`): copia `models/model.joblib` como contexto adicional y **el build sigue fallando si el SHA-256 no coincide** (`3a741c6`).
- **Defecto encontrado:** el dashboard fallaba en el contenedor con `ModuleNotFoundError: httpx`. `httpx` estaba solo en el grupo `dev` y llegaba de forma transitiva por `openai`; `openai` 3.26 pasó a depender de `httpx2`, y la imagen (`--no-dev`) quedó sin él. Corrección: `httpx` a dependencias de runtime y test `tests/test_packaging.py`, que falla si la API o el dashboard importan algo fuera del cierre transitivo de `[project].dependencies` (comprobado: detecta este caso). 194 tests, 98 % (`1b300a2`).
- Resultado: `verify-docker.ps1 -LocalModel` completo y dashboard operativo en `http://localhost:8501`, según confirmación del responsable.
- Pendiente: repetir con el Release publicado (variante por defecto, la que usará Hugging Face) y CI en verde tras el push.

### S12 — Semana 8: despliegue, monitoreo simulado y cierre

| Campo | Valor |
|---|---|
| Fecha de apertura | 7 de octubre de 2026 |
| Fechas planificadas | 23–29 de noviembre de 2026 |
| Estado | T0 publicada en `d0e8e6c`; T1 y T3–T7 publicadas en `fd78f59` (CI en verde); pendientes del responsable: T2, GIF y etiqueta `v1.0.0` |
| Objetivo | Demo pública en Hugging Face Spaces, monitoreo simulado preregistrado y cierre del portafolio |
| Base | `30c0809`; T0 publicado en `d0e8e6c` y estado final en `fd78f59`, ambos con CI remoto en verde |

| Tarea | Estado | Commit requerido |
|---|---|---|
| T0 | Publicada (`d0e8e6c`, CI remoto en verde) | `docs: spec 006 deployment and monitoring, week 8 plan (SDD gate)` |
| T1 | Implementada y publicada en `fd78f59`; despliegue público pendiente | `build: hugging face space sync` |
| T2 | Pendiente del responsable (B-03) | `docs: public deployment verified` |
| T3 | Implementada y publicada en `fd78f59`; secretos del Space pendientes | `feat: rate limit for optional LLM` |
| T4 | Completada y publicada en `fd78f59` | `feat: simulated drift monitoring` |
| T5 | Publicada en `fd78f59`, salvo el GIF (responsable) | `docs: final portfolio readme` |
| T6 | Publicada en `fd78f59`; `docker build` con el Release pendiente del responsable | `chore: final cleanup and reproducibility check` |
| T7 | Documentación completada; etiqueta `v1.0.0` pendiente | `docs: week 8 close and project completion` |

**Nota de proceso.** Por decisión del responsable, Claude edita la carpeta de trabajo y el responsable hace los commits al final. La compuerta SDD se respeta en el orden del historial (T0 primero), pero no en el tiempo: el código se escribió antes del commit de la spec. Solo se verificó el estado final; los commits intermedios no se probaron uno por uno.

#### T0 — Compuerta

- Decisiones del responsable (7 de octubre de 2026): **D1 = A** (PSI + KS/chi² propios, sin Evidently), **D2 = A** (LLM activado con límite por hora y plantilla de respaldo) y **D3** Space público `<usuario-hf>/bank-churn-ml`.
- **B-03:** el responsable aún no tiene cuenta de Hugging Face; se usa `darwinjaco` como usuario provisional (README, `deploy/space/README.md`). El código no depende del nombre: el workflow usa la variable `HF_SPACE`.
- Spec 006 v1.0 y [plan de semana 8](plan-semana-8.md). Umbrales de PSI, escenarios, expectativas E1–E4 y **notas a priori** (§4.7: PSI analítico ≈ 0,20 en S3 y ≈ 0,27 en S2; Brier sensible a la mezcla) escritos antes de ejecutar el monitoreo.
- Decisión de diseño tomada en T0, no como contingencia: el Dockerfile del Space se deriva solo con la variante `release` (D-19), porque el contexto `localmodel` no existe en el builder de Hugging Face.

#### T1 — Sincronización con Hugging Face

- `scripts/build_space.py` (solo biblioteca estándar): copia `pyproject.toml`, `uv.lock`, `src/churn/*.py`, `dashboard/*.py`, `docker/start.sh`, `model_metadata.json`, `final_test.json`, `monitoring.json` y el README del Space; deriva el Dockerfile (cada sustitución debe ocurrir exactamente una vez) y falla ante binarios, `data/`, `models/`, `mlruns/`, `.env`, CSV, `.joblib` o `.parquet`.
- `deploy/space/README.md`: cabecera YAML (`sdk: docker`, `app_port: 7860`, `license: mit`, `short_description` de 58 caracteres) y aviso de datos sintéticos y de que no es asesoría financiera.
- `.github/workflows/deploy-space.yml`: `workflow_dispatch` y etiquetas `v*`; falla si faltan `HF_TOKEN` o `HF_SPACE`; el token solo se expone en los dos pasos que lo usan, nunca en `checkout` ni `setup-python`.
- `tests/test_build_space.py` (13 tests): lista exacta de archivos, cabecera YAML, Dockerfile solo `release`, cada `COPY` del Dockerfile existe en el Space, detección de cambios incompatibles y rechazo de seis tipos de archivo prohibido.

#### T3 — Límite del LLM

- `narrative.py`: `HourlyLimiter` (ventana deslizante de 3.600 s, en memoria, con *lock*) y `LLM_MAX_CALLS_PER_HOUR` (vacío = 30; 0 desactiva; valor no entero o negativo → 30). Cuenta también los intentos fallidos. Sobre el límite → plantilla con `reason="límite de llamadas por hora"`.
- Tests: límite, intentos fallidos, ventana deslizante con reloj simulado, 0 desactiva y siete casos de lectura de la variable. `.env.example` y `docker-compose.yml` actualizados.
- Pendiente del responsable: secretos `LLM_BASE_URL`, `LLM_API_KEY` y `LLM_MODEL` en el Space y comprobar `source="llm"` en la demo.

#### T4 — Monitoreo simulado

- `src/churn/monitoring.py`, CLI `churn-monitor` → [`reports/monitoring.md`](../reports/monitoring.md), `reports/monitoring.json` y `reports/figures/monitoring_psi.png` (47 KB). Carga solo con `load_exploration()` (entrenamiento y validación); un test comprueba que el módulo no menciona la partición de prueba y otro que `load_partitions()` excluye sus filas.
- Control de reproducibilidad: S0 reproduce `decision.json` (621 contactados, 61.950 €).

| | S0 | S1 Age | S2 Germany | S3 inactivos | S4 prevalencia |
|---|---|---|---|---|---|
| PSI máximo (variable) | 0,006 | **0,327** Age | **0,275** Geography | 0,196 IsActiveMember | 0,023 Age |
| PSI probabilidad | 0,000 | 0,081 | 0,055 | 0,014 | 0,039 |
| Calibración global | +0,3 pp | +1,4 pp | −0,7 pp | −0,1 pp | **−9,6 pp** |
| Brier / S0 | 1,00 | 1,09 | **1,18** | 1,02 | **1,40** |
| Tasa de contacto | 31,1 % | 42,2 % | 38,2 % | 34,9 % | 38,6 % |

- **E1 cumplida.** **E2 no cumplida:** S3 queda en 0,196 (nota a priori ≈ 0,20); S1 y S2 sí alarman con calibración dentro de ±3 pp. **E3 cumplida:** la prevalencia del 35 % descalibra el modelo −9,6 pp sin ninguna alarma de PSI. **E4 cumplida** (+3,8 a +11,1 pp).
- S2 figura como "degradación" solo por el Brier (1,18 × S0) con la calibración dentro de rango: es el efecto de mezcla anticipado en la nota 3 de §4.7, no un deterioro del modelo. Se reporta sin reinterpretar el criterio.
- `monitoring.json` registra `git_commit` = `30c0809`, el HEAD al generarlo (el código se publicó después en `fd78f59`); los resultados son deterministas (semilla 2028) y se pueden regenerar con `uv run churn-monitor`.
- Opcional de §4.9 implementado: `GET /monitoring` y pestaña **Monitoreo** del dashboard.
- Tests (11): PSI = 0 con distribuciones idénticas, PSI calculado a mano (0,16946), ε en bins vacíos, deciles con masa puntual en cero e intervalos cerrados por la derecha, escenarios deterministas que alcanzan la proporción objetivo, E1/E3 reproducidas con datos sintéticos, sin partición de prueba y CLI con reportes.

#### T5 — README final y ejemplo

- README de portafolio: resumen en inglés, resultados de prueba y políticas, diagrama Mermaid, tabla de etapas con evidencia, monitoreo, decisiones técnicas, limitaciones, trabajo futuro e inicio rápido. Las secciones semanales pasan a [`docs/historial-semanal.md`](historial-semanal.md) sin cambios de contenido (solo rutas relativas).
- `examples/clientes_ejemplo.csv`: 20 clientes **sintéticos** generados por `scripts/make_example_csv.py` (semilla 20261123), con identificadores ficticios `EJ-01…` y ningún cliente alemán con saldo cero (regularidad de H5). Tests: el archivo coincide con el generador y cada fila pasa el contrato de la API. Con el modelo real: 13 de 20 a contactar.
- Pendiente del responsable: GIF de demo (20–30 s; si supera 500 KB, como asset de un Release).

#### Revisión completa del código (T6)

| # | Hallazgo | Corrección |
|---|---|---|
| 1 | `Balance` o `EstimatedSalary` NaN o infinito → **HTTP 500**: FastAPI no podía serializar el error 422 que contenía `nan` (afectaba al lote del dashboard con una celda vacía) | `allow_inf_nan=False` y manejador que serializa los valores no finitos; tests con NaN, +inf y lote |
| 2 | Dashboard: un 422 de la API en el lote (edad 15, país desconocido) producía una traza de Python | `ApiError` con mensaje por fila (`fila 4, Age: ...`); todas las llamadas capturadas |
| 3 | `prepare_batch` truncaba `Age = 52.7` a 52 sin aviso y dejaba pasar celdas vacías | Rechazo explícito de vacíos, no numéricos y decimales en columnas enteras |
| 4 | El explicador SHAP se creaba en cada petición, contra la spec 005 §6 | Se crea una vez por proceso, al arrancar (`Service.explainer`) |
| 5 | Pestaña Monitoreo: columnas con texto y números rompían la conversión a Arrow (encontrado en la prueba de humo) | Valores formateados como texto; test con `pyarrow` |
| 6 | `verify-docker.ps1` imprimía resultados sin comprobarlos y no probaba la imagen del Space | Aserciones (SHA-256, 0,947, contactar, 422, `/explain`, `/monitoring`) y etapa `ROLE=all` con el Dockerfile derivado |
| 7 | Cliente HTTP nuevo en cada re-ejecución de Streamlit | `st.cache_resource` |
| 8 | Versión del paquete 0.1.0 frente a la etiqueta prevista `v1.0.0` | 1.0.0 en `pyproject.toml`, `uv.lock` (`uv lock --check` en verde), `__init__` y la API |
| 9 | Documentación desactualizada: §2, §3, S07 y S08 de este registro; ruta local absoluta en `contexto-proyecto.md`; `.env.example` con un valor; la spec 006 contenía literalmente los patrones de secretos que debía buscar | Actualizados; patrones escritos con `[-]`/`[/]` para que la búsqueda no se encuentre a sí misma |

Sin defectos en los módulos de análisis (semanas 2–6): ya produjeron los resultados versionados y conservan sus protecciones (`InputGuard`, `load_test_once`, hashes). Los 147 avisos de pytest son deprecaciones de terceros (SHAP, MLflow) y el `penalty="l2"` ya registrado como trabajo futuro.

**Comprobaciones ejecutadas (Linux, Python 3.11.16, entorno aparte; nunca sobre el `.venv` de Windows):**

- Carpeta de trabajo (con CSV y modelo): `uv sync --locked --all-groups`; `ruff check .` y `ruff format --check .` en verde; `pytest --cov=churn --cov-fail-under=85`: **243 aprobados, 98,25 %**. `uv lock --check` en verde.
- Prueba de humo con el modelo real: `uvicorn` + `AppTest` del dashboard. `/health` con el SHA-256 publicado; cliente de referencia **94,7 % y contactar**; cuatro pestañas sin excepciones; lote de ejemplo 13/20; lote inválido → mensaje por fila.
- **Clon limpio** (`git clone` de `30c0809` + cambios versionables; sin CSV, modelo ni `mlruns`): `uv sync --locked --all-groups`; Ruff y formato en verde; hooks de pre-commit en verde (trailing-whitespace, end-of-file, check-yaml, check-toml, archivos > 500 KB, claves privadas y nbstripout; ejecutados con las mismas versiones instaladas desde PyPI porque el proxy del entorno bloquea `git fetch` de GitHub); `pytest`: **240 aprobados, 3 omitidos** (CSV y modelo ausentes, como en CI), **98,16 %**; `build_space.py`: 41 archivos, 792 KB.
- Búsquedas en el clon: rutas absolutas → solo la de `contexto-proyecto.md` (corregida); secretos → solo el texto de la spec 006 (reescrito); CSV versionados → solo `examples/clientes_ejemplo.csv`; TODO/FIXME → ninguno en archivos de texto; notebook sin salidas.
- **No verificado aquí:** `docker build` (el entorno no tiene Docker), CI remoto y despliegue público.

#### Comprobaciones para publicación desde Windows

- Solicitud del responsable: subir todos los cambios de la semana 8. Se consolida
  la publicación en dos commits según la enmienda del plan: T0 primero y el estado
  final después. Se mantiene la desviación temporal de SDD ya documentada.
- CI remoto de la base `30c0809` confirmado en verde antes de versionar:
  https://github.com/darwinjaco/bank-churn-ml/actions/runs/37568126713.
- Comandos ejecutados: `git status -sb`, `git diff --stat`,
  `git log --oneline -10`, `git remote -v`, `git diff --check`, revisión del diff
  de código y configuración, y `gh run list --branch main --limit 5 --json databaseId,headSha,status,conclusion,workflowName,url`.
- `uv sync --locked`, `uv run ruff check .` y `uv run ruff format --check .`:
  sincronización, lint y formato satisfactorios.
- `git add --all` seguido de `uv run pre-commit run --all-files`: todos los hooks
  en verde, incluidos los archivos nuevos. Búsqueda de secretos con
  `git grep --cached -l -I -E` sin coincidencias; `git ls-files "*.csv"` devuelve
  únicamente el ejemplo sintético.
- Primeras ejecuciones de `uv run pytest --cov=churn --cov-report=term-missing --cov-fail-under=85`
  bloqueadas por paquetes incompletos del entorno local (`python-dateutil` y
  `protobuf`). Se ejecutó `uv sync --locked --reinstall-package python-dateutil`
  y después `uv sync --locked --all-groups --reinstall`, sin cambiar dependencias
  ni el lockfile. Ruff y formato repetidos tras reparar el entorno: en verde.
- Suite completa con el comando requerido: **243 aprobados, cobertura 98,25 %**
  (mínimo 85 %), 147 avisos de terceros ya documentados. La evaluación final real
  no se volvió a ejecutar; los tests de esa ruta usan datos sintéticos.
- `git commit -m "docs: spec 006 deployment and monitoring, week 8 plan (SDD gate)"`
  y `git push origin main`: T0 publicado como `d0e8e6c`, con hooks satisfactorios.
  `gh run watch 37571345750 --exit-status --interval 10`: CI remoto en verde
  (1 min 22 s), antes del commit consolidado del estado final:
  https://github.com/darwinjaco/bank-churn-ml/actions/runs/37571345750.
- Siguiente paso: publicar el estado final y comprobar el CI de ese commit y la
  sincronización con `origin/main`. T1 y T3–T7 se agrupan conforme a la enmienda
  del plan; el despliegue público, el GIF y la etiqueta conservan sus pendientes.

#### Revisión de los seis pasos de cierre

- `git status -sb`: `main` sincronizada con `origin/main` en `fd78f59`, árbol
  limpio al comenzar la revisión. `gh run view 37571530333 --json headSha,conclusion,url`
  confirma CI remoto satisfactorio para ese commit:
  https://github.com/darwinjaco/bank-churn-ml/actions/runs/37571530333.
- `gh release list --limit 10` y
  `gh api repos/darwinjaco/bank-churn-ml/releases`: no existen releases.
  `Get-FileHash -LiteralPath "models/model.joblib" -Algorithm SHA256` confirma
  que el artefacto local coincide con el SHA-256 fijado (`579b7fe3…095a`).
  El Release `model-v1.0` sigue pendiente.
- `docker version` y `docker compose ps`: Docker Desktop operativo y servicios
  locales levantados. Se ejecutó exactamente `pwsh -File scripts/verify-docker.ps1`
  sin `-LocalModel`: falla en el paso 2 porque no existe el asset del Release;
  no alcanza `VERIFICACIÓN COMPLETA` ni ejecuta los builds de esta verificación.
- Peticiones reales con `Invoke-RestMethod` a `/health` y `/predict` de la API
  local: hash esperado y cliente de referencia con **0,947001474187885**,
  `contact=true`. Esta evidencia es local, no una validación del Space público.
- `gh variable list --json name` y `gh secret list --json name`: listas vacías;
  faltan `HF_SPACE` y `HF_TOKEN`. Consulta pública del Space provisional:
  API de Hugging Face devuelve 401 y `/_stcore/health` devuelve 404. No se puede
  confirmar la cuenta ni un Space público activo con ese nombre.
- `gh run list --workflow deploy-space.yml --limit 5 --json databaseId,status,conclusion,url`:
  ninguna ejecución de *Deploy Space*. T2 continúa pendiente.
- Búsqueda local de `*.gif`, `*.mp4` y `*.webm`: sin archivos. El README contiene
  solo el comentario reservado para el GIF; no hay asset de demo en releases.
- `git tag --list`: sin etiquetas locales; consulta de referencias de etiquetas
  en GitHub devuelve 404 y la lista de releases está vacía. `v1.0.0` sigue pendiente.
- Desviación de trazabilidad confirmada: **dos commits en lugar de los siete
  previstos**, T0 = `d0e8e6c` y T1/T3–T7 = `fd78f59`. La consolidación está
  documentada en el plan; es una excepción a «una tarea = un commit». Se conserva
  también la desviación temporal de SDD indicada en la nota de proceso.
- Siguiente paso: publicar `model-v1.0` con el artefacto verificado, repetir la
  verificación Docker y configurar la cuenta/Space de Hugging Face para T2.

#### Pendientes del responsable (en orden)

1. **Completado:** publicación de semana 8 en `fd78f59` y CI remoto en verde.
2. Release `model-v1.0` con `models/model.joblib` (repositorio público: confirmado por la API de GitHub).
3. `pwsh -File scripts/verify-docker.ps1` sin `-LocalModel`: ahora incluye la imagen del Space.
4. Cuenta y token de Hugging Face (B-03); crear el Space vacío (Docker, *Blank*, público); secreto `HF_TOKEN` y variable `HF_SPACE` en GitHub; si el usuario no es `darwinjaco`, corregir README y `deploy/space/README.md`.
5. Ejecutar *Deploy Space* (T2) y verificar §2.5; secretos del LLM en el Space (T3).
6. GIF de demo (T5) y etiqueta/Release `v1.0.0` (T7).

### S13 — Revisión previa a producción: correcciones de documentación

| Campo | Valor |
|---|---|
| Fecha | 2026-10-07 |
| Fase | Cierre (posterior a la semana 8) |
| Estado | En revisión: correcciones de documentación comprobadas en local y propuestas en la rama `docs/pre-production-review` (sin los cambios de Render); decisiones D-A y D-B pendientes |
| Objetivo | Revisar [`verificacion-preproduccion.md`](verificacion-preproduccion.md) y alinear la documentación con el estado publicado (`fd78f59`, CI remoto en verde) |

**Trabajo realizado**
- Plan de revisión corregido: el `git stash -u` ahora se limita a los 7 archivos de la preparación de Render (antes se habría llevado el propio plan y este registro); comprobaciones alineadas con `AGENTS.md` §4; regla de reproducibilidad contra JSON versionados sin reentrenar ni ejecutar `churn-final`; módulos y archivos que faltaban en la tabla por semana; corrección 7 de S12/T6; notas sobre `penalty`, `git_commit` de `monitoring.json`, tamaño de la imagen y `ROLE=all` de `deploy/Dockerfile.release`.
- Estados desactualizados tras publicar `fd78f59`: §2 (semanas 7–8), §3 (specs 005–006), S11 (estado y T7 = `5b391f9`), S12 (estado, T3, T5, T6 y nota de `git_commit` de T4), spec 005 (criterio de CI marcado), spec 006 (estado y criterio 1) y `contexto-proyecto.md` (base, pendiente 1, excepción de la semana 8 a «una tarea = un commit» y comando de pytest).
- `penalty="l2"`: «obsoleto en scikit-learn 1.10» → «obsoleto desde scikit-learn 1.9; se elimina en la 1.10» (versión bloqueada 1.9.1) en README y `contexto-proyecto.md`.
- README: el enlace a la demo indica «pendiente de publicar» (el Space no existe).

**Archivos modificados o creados**
- `docs/verificacion-preproduccion.md`, `docs/registro-avance.md`, `docs/contexto-proyecto.md`, `README.md`, `specs/005-api-and-dashboard.md`, `specs/006-deployment-monitoring-release.md`.

**Comprobaciones y evidencia**
- `gh run list --branch main --limit 3`: CI satisfactorio en `fd78f59`, `d0e8e6c` y `30c0809`. `docker images`: `bank-churn-ml:space` y `bank-churn-ml:local` de 3,34 GB. `uv.lock`: scikit-learn 1.9.1.
- `uv sync --locked`; `uv run ruff check .`: **1 error** E501 en `tests/test_build_space.py:116`, archivo de la preparación de Render sin commit (no modificado aquí). `uv run ruff format --check .`: en verde.
- `uv run pre-commit run --files` sobre los seis archivos editados: en verde.
- `uv run pytest --cov=churn --cov-report=term-missing --cov-fail-under=85`: **246 aprobados, 98,22 %** (243 + 3 tests de la preparación de Render), 147 avisos de terceros ya documentados. Después, `uv sync --locked --all-groups` para restaurar el grupo `eda`.
- Comprobación solo local; sin commit ni CI remoto de estos cambios.

**Decisiones y pendientes**
- **D-A (responsable):** aparcar los cambios de Render con el stash limitado del plan §4 o continuar con Render, lo que exige antes la enmienda v1.1 de la spec 006 con commit (`AGENTS.md` §6). Mientras tanto, `ruff check .` no queda en verde por el E501 de esos cambios.
- **D-B (responsable):** confirmar la autoría de la sección «Revisión de los seis pasos de cierre» y de las líneas de estado de S12, pendientes y CI/CD añadidas por otra sesión; su contenido coincide con git y GitHub.
- Siguiente paso: resolver D-A y D-B, repetir las comprobaciones con `pre-commit run --all-files` y hacer commit (`docs: pre-production review corrections`) con CI remoto en verde.

## 6. Estado del proyecto y Definition of Done

Estado al 7 de octubre de 2026, contra la *Definition of Done* del plan maestro (punto 37). ✅ = verificado; ⏳ = implementado, falta una acción externa del responsable; ↔ = desviación justificada.

| Ítem | Estado | Evidencia o justificación |
|---|---|---|
| Dataset documentado | ✅ | [spec 001](../specs/001-overview-and-data-contract.md) §2 y §6; [calidad](../reports/data_quality.json) |
| Data contract definido | ✅ | Spec 001 §4–5; Pandera (`validation.py`) y Pydantic en la API |
| SDD completo | ✅ | Specs 001–006 con enmiendas versionadas; planes semanales en `docs/` |
| EDA terminado | ✅ | [Notebook](../notebooks/01_eda.ipynb) delgado y figuras generadas por código |
| Hipótesis analizadas | ✅ | H1–H6 preregistradas ([reporte](../reports/eda_hypotheses.md)) |
| Preprocessing reproducible | ✅ | `pipeline.py`: `ColumnTransformer` aprendido solo en entrenamiento; `InputGuard` rechaza `Gender` |
| Feature engineering documentado | ✅ | Spec 002: FS-RAW, FS-EDA y FS-TREE; `features.py` sin estado externo |
| Train/Validation/Test definido | ✅ | 60/20/20 estratificado, semilla 42, [manifiesto](../reports/split_manifest.json) con hashes |
| Baseline implementado | ✅ | Dummy y LogReg ([baselines](../reports/baselines.md)) |
| Logistic Regression | ✅ | FS-RAW y FS-EDA; FASE B 0,655 ± 0,027 |
| Random Forest | ✅ | Modelo final; FASE B 0,686 ± 0,018 |
| XGBoost | ✅ | FASE B 0,697 ± 0,018; descartado por parsimonia (regla §6 preregistrada) |
| Neural Network (opcional) | ↔ | No evaluada: 10.000 filas tabulares y regla de parsimonia; registrada como desviación en el README |
| Cross-validation | ✅ | Estratificada; FASE B 5×2 con pliegues nuevos (semilla 2027) |
| Hyperparameter tuning | ✅ | `RandomizedSearchCV` con espacios preregistrados ([tuning](../reports/tuning.json)) |
| Experiment tracking | ✅ | MLflow con commit, hash del CSV y del manifiesto en cada corrida (local, fuera de Git) |
| Métricas comparadas | ✅ | [Selección](../reports/model_selection.md): AP, ROC-AUC, Brier y log loss por familia |
| Threshold optimizado | ↔ | Umbral **analítico** t\* = c/(s·V) = 1/6 (spec 004), no ajustado con datos para no sobreajustarlo; opciones B y C como trabajo futuro |
| Calibration evaluada | ✅ | E-04: sigmoide elegida por Brier; curvas de fiabilidad |
| SHAP | ✅ | Global, por grupos y local con aditividad comprobada; 3 razones por cliente en la API |
| Error analysis | ✅ | Perfiles VP/FP/FN/VN y zona del umbral ([auditoría](../reports/audit.md)) |
| Segment analysis | ✅ | Geografía, edad, productos, actividad, saldo y E-01 por género (alerta en precisión documentada) |
| Modelo serializado | ✅ | `CalibratedModel` (pipeline + calibrador) en `model.joblib`, SHA-256 fijado; metadata versionada |
| Pipeline de inferencia | ✅ | `api.Service` (en lugar del `predict.py` del plan); devuelve probabilidad, decisión y beneficio en vez de un `risk_level` arbitrario |
| FastAPI | ✅ | Spec 005 v1.1; 20 tests de API |
| Streamlit | ✅ | Cuatro pestañas; prueba de humo con `AppTest` y la API real |
| Tests | ✅ | 243 tests (98,25 %); 240 + 3 omitidos en un clon limpio sin datos (98,16 %) |
| Linting | ✅ | Ruff, formato y hooks de pre-commit en verde (S12) |
| Docker | ⏳ | Verificado en Windows con el modelo local (S11); falta repetirlo con el Release y la imagen del Space |
| CI/CD | ⏳ | Semanas 7–8 publicadas; CI de `fd78f59` en verde. Workflow *Deploy Space* sin ejecuciones; faltan `HF_TOKEN` y `HF_SPACE` |
| Deployment | ⏳ | Space pendiente de la cuenta de Hugging Face (B-03) |
| README profesional | ⏳ | Redactado; faltan el GIF y la URL pública activa |
| Reproducibilidad verificada | ✅ / ⏳ | Pipeline completo reproducido desde un clon limpio (S08–S10); tests y hooks desde un clon limpio (S12); `docker build` desde un clon limpio pendiente |

**Lo que aporta el proyecto más allá del checklist:** decisión económica explícita en lugar de una métrica aislada, preregistro de hipótesis, reglas y umbrales (con expectativas que se reportan aunque no se cumplan, como E2), una única evaluación en prueba protegida por código, y un monitoreo que demuestra un límite real: el cambio de prevalencia degrada el modelo sin alarmas de entrada.

## 7. Plantilla para nuevas secciones

```markdown
### SXX — Nombre de la sección

| Campo | Valor |
|---|---|
| Fecha | AAAA-MM-DD |
| Fase | Semana N |
| Estado | Pendiente / En curso / Completada / Bloqueada |
| Objetivo | Resultado concreto esperado |

**Trabajo realizado**
- Tareas terminadas.

**Archivos modificados o creados**
- Rutas relevantes.

**Comprobaciones y evidencia**
- Comando o revisión, resultado y enlace o ruta de evidencia.

**Decisiones y pendientes**
- Decisiones adoptadas, limitaciones y bloqueos reales.

**Siguiente paso**
- Próxima acción concreta.
```
