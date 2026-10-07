# Plan de trabajo — Semana 8 (23–29 de noviembre de 2026)

| Campo | Valor |
|---|---|
| Especificación | [006 — Despliegue, monitoreo simulado y cierre](../specs/006-deployment-monitoring-release.md) v1.0 |
| Decisiones del responsable | D1 = A (PSI + KS/chi² propios); D2 = A (LLM con límite por hora); D3 = Space público `<usuario-hf>/bank-churn-ml` (usuario provisional `darwinjaco`, B-03) |
| Prioridad si falta tiempo | (1) despliegue, (2) README final, (3) cierre, (4) monitoreo (lo primero que se recorta) |

| Tarea | Entregable | Commit |
|---|---|---|
| T0 | Spec 006, este plan, registro S12 | `docs: spec 006 deployment and monitoring, week 8 plan (SDD gate)` |
| T1 | `deploy/space/README.md`, `scripts/build_space.py`, `.github/workflows/deploy-space.yml`; tests | `build: hugging face space sync` |
| T2 | Workflow ejecutado, Space verificado en la URL pública (responsable) | `docs: public deployment verified` |
| T3 | Límite `LLM_MAX_CALLS_PER_HOUR` en `narrative.py`; tests; `.env.example` | `feat: rate limit for optional LLM` |
| T4 | `monitoring.py`, CLI `churn-monitor`, reportes y figura; `GET /monitoring` y pestaña opcional; tests | `feat: simulated drift monitoring` |
| T5 | README final, `examples/clientes_ejemplo.csv` sintético y su generador; GIF (responsable) | `docs: final portfolio readme` |
| T6 | Verificación desde clon limpio, búsquedas vacías, limpieza y correcciones de la revisión | `chore: final cleanup and reproducibility check` |
| T7 | Spec 006 con evidencia, registro S12, contexto de cierre, tabla de la Definition of Done, etiqueta `v1.0.0` | `docs: week 8 close and project completion` |

Responsable de acciones externas (no automatizables desde el entorno de Claude): push, Release `model-v1.0`, `verify-docker.ps1`, cuenta y token de Hugging Face, secretos de GitHub y del Space, ejecución del workflow, GIF y etiqueta `v1.0.0`.

## Agrupación de archivos por commit (forma de trabajo del 7 de octubre de 2026)

Claude editó la carpeta de trabajo y el responsable versiona al final. Los archivos que mezclan una tarea con correcciones de la revisión (`api.py`, `ui.py`, `dashboard/app.py`) van en la primera tarea que los necesita, para que ningún commit importe código que todavía no existe. Solo el estado final está verificado (S12); el CI evalúa el commit publicado.

| Commit | Archivos |
|---|---|
| T0 | `specs/006-deployment-monitoring-release.md`, `docs/plan-semana-8.md` |
| T1 | `deploy/`, `scripts/build_space.py`, `.github/workflows/deploy-space.yml`, `tests/test_build_space.py` |
| T3 | `src/churn/narrative.py`, `tests/test_narrative.py`, `.env.example`, `docker-compose.yml` |
| T4 | `src/churn/monitoring.py`, `src/churn/plots.py`, `src/churn/explain.py`, `src/churn/api.py`, `src/churn/ui.py`, `src/churn/__init__.py`, `dashboard/app.py`, `tests/test_monitoring.py`, `tests/test_api.py`, `tests/test_ui.py`, `reports/monitoring.json`, `reports/monitoring.md`, `reports/figures/monitoring_psi.png`, `Dockerfile`, `pyproject.toml`, `uv.lock` |
| T5 | `README.md`, `docs/historial-semanal.md`, `examples/`, `scripts/make_example_csv.py`, `tests/test_examples.py` |
| T6 | `scripts/verify-docker.ps1`, `specs/005-api-and-dashboard.md` |
| T7 | `docs/registro-avance.md`, `docs/contexto-proyecto.md` |

T2 (`docs: public deployment verified`) se versiona después del despliegue, con la URL, el tiempo de build y el tamaño de la imagen.

### Publicación consolidada solicitada por el responsable

Para subir todos los cambios ya preparados, se publican dos commits: primero T0
(especificación y plan), y después el estado final de T1 y T3–T7, incluido el
registro de comprobaciones. Se exige CI remoto en verde antes de cada commit y
se comprueba el CI del estado final tras el push. La consolidación cambia solo
la agrupación del historial; los pendientes externos conservan su estado.
