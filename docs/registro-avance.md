# Registro de avance

Documento de seguimiento del proyecto **Abandono bancario → Decisiones de retención**. Se actualiza al terminar cada sección de trabajo y enlaza la evidencia que permite cerrar una fase.

| Campo | Valor |
|---|---|
| Responsable | Darwin Jacome Cuenca |
| Inicio previsto | 5 de octubre de 2026 |
| Fin previsto | 29 de noviembre de 2026 |
| Dedicación estimada | 8 horas por semana; 64 horas en total |
| Última actualización | 6 de octubre de 2026 |
| Fase actual | Semana 2: T5, resultados reales y figuras |

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
| Semana 2 | 12–18 oct | EDA, hipótesis y auditoría de productos 3–4 y balance cero | Hipótesis contrastadas con pruebas estadísticas, tamaños de efecto e incertidumbre | En curso; ejecución iniciada el 6 de octubre |
| Semana 3 | 19–25 oct | Pipeline, división estratificada, Dummy/LogReg y MLflow | Modelos de referencia registrados en MLflow | Pendiente |
| Semana 4 | 26 oct–1 nov | RF, XGBoost, validación cruzada y ajuste acotado | Tabla de media ± desviación estándar por modelo | Pendiente |
| Semana 5 | 2–8 nov | Calibración, umbral monetario, lift y beneficio por decil, sensibilidad | Umbral justificado por beneficio esperado bajo supuestos explícitos | Pendiente |
| Semana 6 | 9–15 nov | SHAP, errores, segmentos y ficha del modelo | Limitaciones documentadas | Pendiente |
| Semana 7 | 16–22 nov | FastAPI, Streamlit, tests de API y Docker Compose | `docker compose up` funciona desde cero | Pendiente |
| Semana 8 | 23–29 nov | Cambio de distribución simulado, despliegue y README final | URL pública y reproducibilidad verificadas | Pendiente |

**Prioridad de alcance:** proteger la capa de decisión de la semana 5. Si hay retrasos, reducir primero el monitoreo de cambios de distribución de la semana 8 y registrar el ajuste.

## 3. Seguimiento de especificaciones

| Especificación | Tema | Estado | Momento previsto |
|---|---|---|---|
| 001 | Visión general y contrato de datos | Completada: verificación local y remota | Semana 1 |
| 002 | Modelado y evaluación | Documentada en español; implementación pendiente | Semanas 3–5 |
| 003 | [EDA e hipótesis preregistradas](../specs/003-eda-and-hypotheses.md) | Aprobada v1.0; H1–H6 congeladas al versionar T0 | Semana 2 |
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
| Estado | En curso: T5 |
| Objetivo | Generar los entregables de EDA y detenerse para revisión al terminar T7 |

| Tarea | Estado | Commit requerido |
|---|---|---|
| T5 | Verificada localmente; CI del commit por confirmar | `chore: generate split manifest, hypothesis results and figures` |
| T6 | Pendiente | `docs: EDA notebook` |
| T7 | Pendiente | `docs: week 2 conclusions and log` |

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
