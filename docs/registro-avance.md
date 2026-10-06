# Registro de avance

Documento de seguimiento del proyecto **Abandono bancario → Decisiones de retención**. Se actualiza al terminar cada sección de trabajo y enlaza la evidencia que permite cerrar una fase.

| Campo | Valor |
|---|---|
| Responsable | Darwin Jacome Cuenca |
| Inicio previsto | 5 de octubre de 2026 |
| Fin previsto | 29 de noviembre de 2026 |
| Dedicación estimada | 8 horas por semana; 64 horas en total |
| Última actualización | 6 de octubre de 2026 |
| Fase actual | Semana 4: T1–T7 en ejecución (implementación por Claude a petición del responsable) |

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
| Semana 3 | 19–25 oct | Pipeline, división estratificada, Dummy/LogReg y MLflow | Modelos de referencia registrados en MLflow | Baselines implementadas y registradas; revisión pendiente |
| Semana 4 | 26 oct–1 nov | RF, XGBoost, validación cruzada y ajuste acotado | Tabla de media ± desviación estándar por modelo | Compuerta documental en curso; bloqueo B-02 antes de entrenar |
| Semana 5 | 2–8 nov | Calibración, umbral monetario, lift y beneficio por decil, sensibilidad | Umbral justificado por beneficio esperado bajo supuestos explícitos | Pendiente |
| Semana 6 | 9–15 nov | SHAP, errores, segmentos y ficha del modelo | Limitaciones documentadas | Pendiente |
| Semana 7 | 16–22 nov | FastAPI, Streamlit, tests de API y Docker Compose | `docker compose up` funciona desde cero | Pendiente |
| Semana 8 | 23–29 nov | Cambio de distribución simulado, despliegue y README final | URL pública y reproducibilidad verificadas | Pendiente |

**Prioridad de alcance:** proteger la capa de decisión de la semana 5. Si hay retrasos, reducir primero el monitoreo de cambios de distribución de la semana 8 y registrar el ajuste.

## 3. Seguimiento de especificaciones

| Especificación | Tema | Estado | Momento previsto |
|---|---|---|---|
| 001 | Visión general y contrato de datos | Completada: verificación local y remota | Semana 1 |
| 002 | Modelado y evaluación | Baselines implementadas; protocolo de semana 4 v1.2 y bloqueo B-02 | Semanas 3–5 |
| 003 | [EDA e hipótesis preregistradas](../specs/003-eda-and-hypotheses.md) | Implementada v1.1 y revisada; H1–H6 congeladas en v1.0 | Semana 2 |
| 004 | Capa de decisión y beneficio esperado | Pendiente de redacción | Antes de implementar la semana 5 |
| 005 | API y dashboard | Pendiente de redacción | Antes de implementar la semana 7 |
| 006 | Operación: tests, Docker, CI y monitoreo | Pendiente de redacción | Antes de ampliar operación y serving |

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
| Estado | Completada técnicamente; pendiente de revisión |
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
| Estado | En curso: T1; B-02 resuelto y versionado |
| Objetivo | Fijar el protocolo antes de entrenar, comparar familias en FASE B y ejecutar E-03/E-02 sin consultar prueba |

| Tarea | Estado | Commit requerido |
|---|---|---|
| T0 | Completada | `docs: amend spec 002 v1.2 and week 4 plan (SDD gate)` |
| T1 | Completada (`53d909a`; CI tras push) | `fix: baseline report precision and paired differences` |
| T2 | Completada (commit local; CI tras push) | `build: add xgboost` |
| T3 | Pendiente | `feat: tree pipelines and preregistered search spaces` |
| T4 | Pendiente; protocolo OOF bloqueado por B-02 | `feat: two-phase tuning and re-evaluation` |
| T5 | Pendiente | `feat: preregistered model selection rule` |
| T6 | Pendiente; E-02 bloqueada por B-02 | `feat: model selection and ablation experiments` |
| T7 | Pendiente | `docs: week 4 model selection and experiments` |

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

## 6. Plantilla para nuevas secciones

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
