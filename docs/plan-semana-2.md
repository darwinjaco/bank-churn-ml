# Plan de trabajo — Semana 2 (12–18 de octubre de 2026)

| Campo | Valor |
|---|---|
| Especificación | [003 — EDA e hipótesis preregistradas](../specs/003-eda-and-hypotheses.md) |
| Rol de planificación y revisión | Claude |
| Rol de implementación | opencode |
| Presupuesto | 8 h |
| Estado | Aprobado v1.0 |

## Reglas de ejecución

1. **Compuerta SDD:** T0 se hace primero y solo modifica documentación. Ningún archivo en `src/`, `tests/` o `pyproject.toml` cambia hasta que T0 tenga commit.
2. Una tarea = un commit con el mensaje indicado. Comprobaciones locales del `AGENTS.md` en verde antes de cada commit.
3. Si una tarea exige algo que no está en la spec 003, **detenerse** y registrarlo como bloqueo. No improvisar.
4. Al terminar cada tarea, actualizar la sección correspondiente del registro (S04–S06).

## Tareas

### T0 — Gobernanza y compuerta (solo documentación) · 45 min · S04

| Cambio | Motivo |
|---|---|
| Crear `.gitattributes` con `* text=auto eol=lf` y `*.png binary`; ejecutar `git add --renormalize .` | `reports/data_quality.json` aparece modificado solo por finales de línea CRLF (confirmado con `git diff --ignore-cr-at-eol`, sin diferencias) |
| `AGENTS.md`: añadir la regla 6, "Compuerta SDD": no modificar `src/`, `tests/` ni dependencias sin una spec y un plan con commit previo. Los cambios de diseño se hacen como **enmiendas versionadas** de la spec, con motivo en el registro | Convertir la práctica actual en regla verificable |
| `AGENTS.md`: añadir la regla 7, "Partición de prueba": no crear funciones que carguen la prueba hasta la evaluación final de la spec 002 | D-08 |
| Renumerar las specs planificadas en el registro: 003 = EDA e hipótesis; 004 = capa de decisión; 005 = API y dashboard; 006 = operación | La 003 se usa ahora para el EDA |
| Spec 002: cambiar las referencias "especificación 003" (capa de decisión) por "especificación 004" | Coherencia tras renumerar |
| Spec 003: cambiar el estado a "Aprobada v1.0" | Congela H1–H6 |
| Registro: abrir S04 con fecha y objetivo | Trazabilidad |

Commit: `docs: approve spec 003 and week 2 plan (SDD gate)`.

### T1 — Dependencias · 15 min · S05

- Producción: `scikit-learn`, `scipy`, `statsmodels`.
- Grupo nuevo `eda` (no producción): `matplotlib`, `ipykernel`.
- `uv lock` y luego `uv sync --locked --all-groups`. Actualizar el CI a `uv sync --locked --all-groups` solo si los tests lo necesitan (no deberían: los tests no dibujan figuras).

Commit: `build: add stats and EDA dependencies`.

### T2 — División y manifiesto · 1 h 30 min · S05

Archivo: `src/churn/split.py`.

- `make_split(df) -> dict[str, list[int]]`: estratificado por `Exited`, 60/20/20, semilla `RANDOM_SEED`. Primero se separa la prueba (20 %) y luego entrenamiento y validación (75/25 del resto).
- `build_manifest(df, split) -> dict`: tamaños, tasa de abandono por conjunto, semilla, SHA-256 del CSV, SHA-256 de los `CustomerId` ordenados por conjunto, versión de scikit-learn.
- `load_exploration() -> pd.DataFrame`: entrenamiento + validación con una columna `partition`. **No existe** `load_test()`.
- CLI `churn-split`: escribe `data/processed/split.json` y `reports/split_manifest.json`.

Tests (`tests/test_split.py`):

- Sin solapamiento; la unión cubre todas las filas.
- Tamaños 60/20/20 (±1 fila).
- Tasa de abandono por conjunto a ≤ 1 pp de la global.
- Determinismo: dos ejecuciones producen el mismo resultado.
- `load_exploration()` no contiene ningún `CustomerId` de la prueba.
- `realdata`: el split regenerado coincide con `reports/split_manifest.json`.

Commit: `feat: stratified split with versioned manifest`.

### T3 — Funciones estadísticas · 1 h 30 min · S05

Archivo: `src/churn/stats.py`. Funciones puras, sin I/O ni gráficos.

- `wilson_ci(k, n)`, `risk_difference(k1, n1, k2, n2)` (IC Newcombe), `odds_ratio(table)` (IC Woolf), `cramers_v(table)`, `holm(pvalues)`, `auc_bootstrap(score, y, n_boot=2000, seed=42)`.

Tests (`tests/test_stats.py`): los valores de referencia de la spec 003 §9 con tolerancia `1e-4`, más casos borde (n = 0 produce error controlado; tabla con ceros).

Commit: `feat: statistical helpers with reference tests`.

### T4 — Contrastes H1–H6 · 2 h · S05

Archivo: `src/churn/hypotheses.py`.

- Una función por hipótesis, `test_h1(df) … test_h6(df)`, que devuelve un `HypothesisResult` (dataclass: id, prueba, estadístico, p_raw, efecto, ic_low, ic_high, umbral, dirección_ok, detalles).
- `run_all(df)`: ejecuta H1–H6, aplica Holm sobre H1–H5, asigna el veredicto según la spec 003 §4 y devuelve la lista.
- CLI `churn-hypotheses`: `load_exploration()` → `run_all` → `reports/hypotheses.json`.
- Las definiciones (tramos, `balance_10k`, edad centrada) se importan de `config.py`, no se escriben a mano en el código.

Tests (`tests/test_hypotheses.py`):

- Datos sintéticos con un efecto sembrado en H1 → veredicto `confirmada`.
- Datos sin efecto → `no confirmada` (semilla fija).
- Holm aplicado solo a H1–H5; H6 sin p ajustado.
- Ningún módulo nuevo lee `Gender` (test por inspección del código fuente o de las columnas usadas).

Commit: `feat: preregistered hypothesis tests H1-H6`.

### T5 — Ejecución sobre datos reales y figuras · 45 min · S06

- `uv run churn-split` y luego `uv run churn-hypotheses`.
- `src/churn/plots.py` (grupo `eda`): las 6 figuras de la spec 003 §6 en `reports/figures/`. Sin lógica estadística propia: solo dibuja los resultados.
- Se excluye `plots.py` de la medición de cobertura **solo si** no se puede testear sin dependencias gráficas; documentarlo.

Commit: `chore: generate split manifest, hypothesis results and figures`.

### T6 — Notebook narrativo · 45 min · S06

`notebooks/01_eda.ipynb`, delgado: carga con `load_exploration()`, descriptivos (tipos, distribuciones, cardinalidades), muestra `hypotheses.json` y las figuras. Sin funciones definidas en el notebook.

Commit: `docs: EDA notebook`.

### T7 — Conclusiones y cierre · 45 min · S06

- `reports/eda_hypotheses.md`: tabla H1–H6 (efecto, IC, p Holm, veredicto) con una conclusión de una línea cada una, más la sección "Implicaciones para la semana 3" (qué variables derivadas se justifican y qué cambia en E-02 y E-03).
- Spec 001 §6: añadir los hallazgos como Q-06 en adelante.
- README: actualizar los hallazgos y la hoja de ruta.
- Registro: cerrar S04–S06 con comandos, resultados y la URL del CI.

Commit: `docs: week 2 conclusions and log`.

## Revisión de Claude (después de T7)

Se revisa contra la spec 003 §8:

- que el veredicto de cada hipótesis siga la regla de §4;
- que ninguna conclusión sea causal;
- que la prueba no se haya tocado (manifiesto);
- que las implicaciones para la semana 3 estén justificadas por los resultados.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| H3 o H4 mal especificadas en `statsmodels` (fórmula, centrado) | Test con datos sintéticos de coeficiente conocido |
| Tentación de añadir hipótesis al ver resultados | Etiquetarlas como exploratorias en una sección aparte |
| La semana se alarga por las figuras | Las figuras son lo último y tienen máximo 6; los resultados en JSON son lo que cierra la semana |
