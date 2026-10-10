# Revisión integral de las semanas 1–8 — bank-churn-ml

| Campo | Valor |
|---|---|
| Fecha | 7 de octubre de 2026 |
| Commit base | `fd78f59` (CI remoto en verde) |
| Alcance | Buscar errores e incoherencias en código, specs, reportes y registro de las 8 semanas, y corregirlos |
| Fuera de alcance | **Producción / despliegue público**: aplazado (§4) |

## 1. Reglas de la revisión

- Cada hallazgo: archivo y línea, evidencia (salida de consola o valor), corrección y test que lo cubre (si es un hallazgo de código; en documentación basta la evidencia).
- No reentrenar ni cambiar el modelo, el umbral o los supuestos. **No usar la partición de prueba.**
- La reproducibilidad se comprueba contra los JSON versionados: tras ejecutar `churn-validate` o `churn-split`, revisar `git diff reports/`. No ejecutar `churn-baselines`, `churn-tune`, `churn-select`, `churn-decide`, `churn-audit` ni `churn-final` (reentrenan, escriben en MLflow o tocan la prueba). Que `churn-final` se niega a repetirse se comprueba con `tests/test_final_eval.py` (datos sintéticos).
- Los cambios de diseño van como enmiendas versionadas y se registran en una nueva sección del registro (S13).
- Comprobación final, según `AGENTS.md` §4 (opcionalmente también `uv sync --locked --all-groups` para el grupo `eda`):

```powershell
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run pre-commit run --all-files
uv run pytest --cov=churn --cov-report=term-missing --cov-fail-under=85
```

## 2. Qué revisar por semana

| Semana | Revisar | Invariante o prueba |
|---|---|---|
| 1 — Contrato y validación | `config.py`, `data.py`, `validation.py`, spec 001 | El esquema Pandera coincide con la spec (rangos, tipos, `strict`); `churn-validate` reproduce `reports/data_quality.json` |
| 2 — División, EDA e hipótesis | `split.py` (incluido `load_exploration`), `stats.py`, `hypotheses.py`, notebook, spec 003 | `churn-split` reproduce el manifiesto (hashes); H1–H6 iguales a `hypotheses.json`; no existe un lector de prueba fuera de `load_test_once` |
| 3 — Pipelines y baselines | `features.py`, `pipeline.py`, `train.py`, `tracking.py` | Sin fuga: todo lo aprendido se ajusta dentro del pliegue; `InputGuard` rechaza `Gender`; `baselines.json` coherente con `baselines.md` y con el código (sin reentrenar) |
| 4 — Ajuste y selección | `search_spaces.py`, `tune.py`, `selection.py`, `selection_report.py`, `experiments.py`, spec 002 §6 | La regla de selección aplicada literalmente; E-02 y E-03 del registro y del README coinciden con `model_selection.json` |
| 5 — Calibración y decisión | `calibration.py`, `decision.py`, `decision_report.py`, `decide.py`, spec 004 | Calibrador ajustado solo con OOF de entrenamiento; t\* = 1/6 con `>` estricto; beneficios de `decision.json` recalculables a mano |
| 6 — Auditoría y prueba | `explain.py`, `audit.py`, `run_audit.py`, `final_eval.py`, `model_card.py`, `reports.py`, `plots.py` | Aditividad de SHAP; E-01 sin `Gender` en el modelo; `final_test.json` coherente con la ficha; `churn-final` se niega a repetirse (comprobado por tests, sin ejecutarlo) |
| 7 — API, dashboard y Docker | `artifact.py`, `api.py`, `narrative.py`, `ui.py`, `dashboard/app.py`, `Dockerfile`, `docker/start.sh`, `docker-compose.yml`, `docker-compose.local.yml`, `scripts/verify-docker.ps1`, `.dockerignore`, `.env.example`, spec 005 v1.1 | Hash verificado al cargar; 422 ante `Gender`, IDs, NaN e infinitos; nada sensible enviado al LLM |
| 8 — Monitoreo y cierre | `monitoring.py`, `build_space.py`, `.github/workflows/deploy-space.yml`, `deploy/space/README.md`, `scripts/make_example_csv.py`, `examples/clientes_ejemplo.csv`, spec 006, README | Nunca lee la partición de prueba; E1–E4 tal como están preregistradas; las cifras del README salen de los JSON |

**Transversal:** `.github/workflows/ci.yml` y `.pre-commit-config.yaml`; las cifras del README, la ficha del modelo, la spec 006 y el registro coinciden con los JSON; no hay rutas absolutas, secretos ni CSV reales versionados; los estados de §2, §3 y S01–S12 del registro están actualizados.

## 3. Ya corregido en la revisión de la semana 8 (verificar que se mantiene)

NaN o infinito → 422 (antes 500) · errores 422 legibles en el dashboard · decimales y celdas vacías rechazados en el lote · SHAP creado una sola vez · Arrow en la pestaña Monitoreo · aserciones en `verify-docker.ps1` · cliente HTTP con `st.cache_resource` · versión 1.0.0 · estados desactualizados del registro · ruta local en `contexto-proyecto.md`.

## 4. Pendientes conocidos y aparcados

- **Producción (aplazada):** Hugging Face exige plan PRO para Docker. La opción evaluada es Render gratis con dos servicios de 512 MB cada uno. Los valores API ~370 MB y dashboard ~150 MB son orientativos: no hay una medición registrada en este documento que permita darlos por verificados. Requiere la enmienda v1.1 de la spec 006 y una prueba con `--memory=512m`. `deploy/Dockerfile.release` arranca con `ROLE=all` y `PORT=7860` (un contenedor con dos procesos: FastAPI y Streamlit, según `docker/start.sh`); con dos servicios hay que fijar `ROLE=api` / `ROLE=dashboard` y configurar `API_URL` en el dashboard para que apunte a la API.
- **Preparación de Render aparcada (D-A resuelta):** las siete rutas siguientes y sus tres tests están guardados en el stash `render-prep`, por decisión del responsable. Su diseño de Render sigue sin aprobar ni versionar: las referencias a "spec 006 v1.1 §2.6" y "Render (§2.1)" no corresponden a la spec vigente, y su retirada del disparador por etiquetas necesita enmienda. El stash se realizó con rutas, sin incluir este documento ni el registro:

  ```powershell
  git stash push -u -m "render-prep" -- deploy/Dockerfile.release scripts/build_space.py .github/workflows/deploy-space.yml src/churn/ui.py dashboard/app.py tests/test_build_space.py tests/test_ui.py
  ```

- **Edición concurrente (autoría confirmada, D-B resuelta):** la sesión de OpenCode que realizó la revisión anterior modificó `docs/registro-avance.md`: la sección "Revisión de los seis pasos de cierre" y las líneas de estado de S12, de los pendientes del responsable y de CI/CD en §6. Esa sesión confirmó su autoría; el contenido coincide con git y GitHub según la revisión registrada.
- **Conocidos, sin corregir:**
  - El parámetro `penalty`, incluido `penalty="l2"`, está obsoleto desde scikit-learn 1.8 (versión bloqueada: 1.9.1) y se elimina en la 1.10; confirmado por la documentación y el aviso de `sklearn/linear_model/_logistic.py`. Migrar a `l1_ratio=0` requiere enmienda.
  - `monitoring.json` registra `git_commit` = `30c0809`, el HEAD en el momento de generarlo; el código que lo produjo se publicó después en `fd78f59` (hijo de `d0e8e6c`).
  - Imagen de 3,34 GB (comprobado con `docker images`). Causa sin medir: `mlflow` y `statsmodels` solo se usan para entrenar y analizar (`tracking`, `train`, `stats`, `hypotheses`, `monitoring`) y podrían salir del runtime; `xgboost` sí hace falta, porque `pipeline.py` lo importa al nivel del módulo y se necesita para deserializar el modelo. Mover dependencias exige enmienda (`AGENTS.md` §6).
  - El GIF de demo y la etiqueta `v1.0.0` siguen pendientes.

## 5. Correcciones de seguridad posteriores a esta revisión

La [spec 007](../specs/007-security-hardening.md) y el
[plan de seguridad](plan-seguridad.md) fueron aprobados y versionados en `6343526`
antes de modificar código. S14 registra la corrección de SEC-01 a SEC-13 y sus
pruebas. No se modifican el modelo, sus dependencias Python ni los resultados
congelados. La revisión de seguridad y la corrección no equivalen al despliegue
público ni a una auditoría de CVE de las dependencias.
