# Plan de trabajo — Semana 6 (9–15 de noviembre de 2026)

| Campo | Valor |
|---|---|
| Especificación | [002](../specs/002-modeling-and-evaluation.md) v1.6 §11 |
| Planificación, implementación y verificación | Claude (a petición del responsable) |
| Presupuesto | ~8 h |

| Tarea | Entregable | Commit |
|---|---|---|
| T0 | Spec 002 v1.6 §11, este plan, registro S10; regla 7 de `AGENTS.md` actualizada para §11.6 | `docs: spec 002 v1.6 and week 6 plan (SDD gate)` |
| T1 | Dependencia `shap` | `build: add shap` |
| T2 | `explain.py`: SHAP global/local con agrupaciones R4 y comprobación de aditividad; tests | `feat: SHAP explanations with grouped features` |
| T3 | `audit.py`: errores en t*, segmentos y E-01 con bootstrap; tests | `feat: error, segment and E-01 fairness audit` |
| T4 | CLI `churn-audit` sobre validación, figura SHAP, `reports/audit.json`; ejecución real y verificación independiente | `chore: explainability and audit results` |
| T5 | `reports/audit.md` y `reports/model_card.md` generados; README; registro | `docs: week 6 audit and model card` |
| T6 | Evaluación final en prueba (§11.6), **solo con confirmación del responsable** | `feat: final test evaluation` |
