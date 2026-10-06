# Plan de trabajo — Semana 5 (2–8 de noviembre de 2026)

| Campo | Valor |
|---|---|
| Especificaciones | [004 — Capa de decisión](../specs/004-decision-layer.md) v1.0; [002](../specs/002-modeling-and-evaluation.md) v1.5 §5.3.1 |
| Planificación, implementación y verificación | Claude (a petición del responsable) |
| Alcance aprobado | Calibración E-04 + umbral analítico (opción A). Sin deciles ni sensibilidad |
| Presupuesto | ~8 h |

## Reglas

1. T0 solo documentación y antes de cualquier código.
2. Una tarea = un commit; Ruff, formato, hooks equivalentes y pytest en verde antes de cada commit.
3. La prueba no se carga. `Gender` nunca como feature.
4. Las cifras de los reportes se generan desde JSON.

## Tareas

| Tarea | Entregable | Commit |
|---|---|---|
| T0 | Spec 004 v1.0, spec 002 v1.5, este plan, registro S09 | `docs: spec 004 decision layer, spec 002 v1.5 and week 5 plan (SDD gate)` |
| T1 | `tracking.manifest_sha256()` canónico, usado por `tracking.provenance()` y `train.py`; test de independencia del fin de línea | `fix: canonical split manifest hash` |
| T2 | `calibration.py`: OOF (5 pliegues, semilla 42), sigmoide, isotónica, elección por Brier con empate < 1e-4; tests con datos sintéticos | `feat: probability calibration (E-04)` |
| T3 | `decision.py`: t* desde `config.py`, beneficio por política (nadie, todos, aleatoria 20 %, modelo, oráculo), métricas en t*; tests con valores conocidos | `feat: expected-profit decision layer (spec 004)` |
| T4 | `decide.py` y CLI `churn-decide`: ajuste final, calibración, decisión en validación, artefacto `models/` + metadata, figura de fiabilidad, MLflow `stage ∈ {calibration, decision}` | `feat: calibrate, decide and freeze artifact` |
| T5 | Ejecución real y verificación independiente (script sin importar `churn`) | `chore: calibration and decision results` |
| T6 | `reports/decision.md` generado, README, spec 002 §8 y spec 004 §9, registro S09 | `docs: week 5 calibration and decision` |
