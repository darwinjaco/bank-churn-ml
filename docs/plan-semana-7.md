# Plan de trabajo — Semana 7 (16–22 de noviembre de 2026)

| Campo | Valor |
|---|---|
| Especificación | [005 — API y dashboard](../specs/005-api-and-dashboard.md) v1.0 |
| Decisiones del responsable | Modelo vía GitHub Release con hash; despliegue en Hugging Face Spaces (Docker); LLM opcional (NVIDIA NIM u OpenRouter) |

| Tarea | Entregable | Commit |
|---|---|---|
| T0 | Spec 005, este plan, registro S11 | `docs: spec 005 api and dashboard, week 7 plan (SDD gate)` |
| T1 | Dependencias: fastapi, uvicorn, streamlit, openai, httpx | `build: add serving dependencies` |
| T2 | `artifact.py`: descarga y verificación por SHA-256 | `feat: model artifact download with hash check` |
| T3 | `api.py`: endpoints, contrato Pydantic, razones SHAP; tests | `feat: FastAPI service` |
| T4 | `narrative.py` y `/explain`: LLM opcional con plantilla; tests | `feat: optional LLM explanation with template fallback` |
| T5 | `dashboard/app.py` (Streamlit) y formato; tests | `feat: Streamlit dashboard` |
| T6 | `Dockerfile`, `docker-compose.yml`, `start.sh`, `.dockerignore`; build y prueba real | `build: docker image and compose` |
| T7 | README, registro, instrucciones del Release | `docs: week 7 api, dashboard and docker` |
