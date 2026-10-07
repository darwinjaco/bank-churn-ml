# Contexto del proyecto — bank-churn-ml

Documento de traspaso para retomar el trabajo en una sesión nueva (Claude, opencode u otra persona). Fecha: 7 de octubre de 2026. Último commit local: `87dc9bc`.

## 1. Qué es

Proyecto de portafolio de Darwin Jacome Cuenca: **predicción de abandono bancario convertida en decisiones de retención**. No se queda en "el modelo tiene X de AUC": calcula a quién conviene contactar y cuánto dinero ahorra frente a no usar modelo.

- Repositorio: https://github.com/darwinjaco/bank-churn-ml (rama `main`)
- Carpeta local (Windows): `C:\Users\ASUS\Desktop\Opencode\bank-churn-ml`
- Dataset: *Churn Modelling* (Kaggle), 10.000 clientes, probablemente sintético. El CSV **no** se versiona (`data/raw/Churn_Modelling.csv`).
- Idioma del repositorio: español (identificadores técnicos en inglés).

## 2. Forma de trabajo (obligatoria)

- **SDD (spec-driven development):** ninguna línea de `src/` o `tests/` sin spec y plan versionados antes. Cada semana empieza con una tarea T0 de solo documentación ("compuerta").
- **Una tarea = un commit**, con el mensaje fijado en el plan. Ruff, formato, hooks y pytest en verde antes de cada commit; cobertura mínima 85 %.
- **Preregistro:** hipótesis, umbrales, reglas de selección y criterios se fijan antes de ver resultados. Cambios = **enmiendas versionadas** con motivo en el registro.
- **Bloqueos:** si algo no está definido en la spec, se detiene el trabajo y se registra como bloqueo (B-01, B-02...).
- **Reglas fijas (`AGENTS.md`):** `Gender` nunca es variable del modelo (solo auditoría); la partición de prueba ya se usó **una sola vez** y no se vuelve a evaluar; CI en verde.
- **Registro de avance:** `docs/registro-avance.md` se actualiza en cada tarea (secciones S01–S11).
- **Reportes:** todas las cifras se generan desde JSON con código, nunca a mano.
- Roles: al inicio Claude planificaba y opencode programaba; desde la semana 4, a petición del responsable, Claude planifica, implementa y verifica.

## 3. Estado por semana

| Semana | Contenido | Estado |
|---|---|---|
| 1 | Repo, uv, Ruff, pytest, pre-commit, CI, contrato de datos (Pandera) | Cerrada |
| 2 | División 60/20/20 (semilla 42, manifiesto con hashes), EDA, hipótesis H1–H6 preregistradas | Cerrada |
| 3 | Pipelines sin fuga, baselines (Dummy, LogReg) y MLflow | Cerrada |
| 4 | Ajuste en dos fases (FASE A búsqueda, FASE B pliegues nuevos 5×2), regla de selección, E-02 y E-03 | Cerrada |
| 5 | Calibración (E-04) y capa de decisión por beneficio esperado (opción A) | Cerrada |
| 6 | SHAP, errores, segmentos, E-01 (género), ficha del modelo y **evaluación final en prueba** | Cerrada |
| 7 | API FastAPI, dashboard Streamlit, Docker, LLM opcional | **Implementada; falta verificar Docker** |
| 8 | Despliegue en Hugging Face Spaces, drift (Evidently) y README final | Sin iniciar |

## 4. Resultados clave

- **EDA:** inactividad (+12 pp de abandono), relación no monótona con productos (2 < 1 < 3–4), Alemania con OR ajustado 2,18, edad en U invertida (pico ~57 años), saldo cero con menos abandono (parcialmente confundido con geografía: ningún alemán tiene saldo 0), salario sin señal.
- **Modelo final:** Random Forest (n_estimators=500, max_depth=10, min_samples_leaf=5, max_features=sqrt), **sin `EstimatedSalary`** (E-03), calibración **sigmoide**. Elegido sobre XGBoost por parsimonia (diferencia 0,011 < desviación 0,018).
- **Regla de decisión:** contactar si p > t\* = c / (s·V) = 50 / (0,30 · 1.000) = **1/6**. Supuestos ilustrativos: V = 1.000 €, c = 50 €, s = 30 %.
- **Evaluación final en prueba (única, 7 oct 2026):** AP 0,705, ROC-AUC 0,862, Brier 0,1017. El modelo contacta a 634 de 2.000 clientes y obtiene **61.600 €** frente a 22.100 € contactando a todos (60,5 % del oráculo). Coincide con validación: sin sobreajuste.
- **Auditoría:** SHAP → Age, NumOfProducts, IsActiveMember, Germany. Los abandonos no detectados son jóvenes y activos (18–29: 65 % no contactados). E-01: igual tasa de contacto y sensibilidad entre géneros; **alerta en precisión** (60 % frente a 42 %) por tasas base distintas.
- **Limitaciones:** datos sintéticos; el grupo de 3–4 productos (~3 %) aporta ~0,08 de AP; supuestos económicos iguales para todos; sin datos de tratamiento (uplift).

## 5. Estructura relevante

```text
specs/        001 contrato · 002 modelado (v1.6) · 003 EDA (v1.1) · 004 decisión · 005 API y dashboard
docs/         registro-avance.md, plan-semana-2..7.md, este archivo
src/churn/    config, data, validation, split, stats, hypotheses, features, pipeline, train,
              search_spaces, tune, selection, experiments, calibration, decision, decide,
              explain, audit, run_audit, final_eval, model_card, artifact, api, narrative, ui
dashboard/    app.py (Streamlit; solo consume la API)
reports/      JSON y Markdown generados (tuning, model_selection, decision, audit, final_test,
              model_card, model_metadata) y figures/
models/       model.joblib (16 MB, fuera de Git) + metadata.json
Dockerfile, docker-compose.yml, docker/start.sh, .dockerignore, .env.example
scripts/verify-docker.ps1
```

CLIs: `churn-validate`, `churn-split`, `churn-hypotheses`, `churn-baselines`, `churn-tune`, `churn-select`, `churn-decide`, `churn-audit`, `churn-final` (ya ejecutado: falla si se repite).

## 6. Semana 7: lo implementado

- **API** (`src/churn/api.py`): `GET /health`, `GET /model`, `POST /predict` (probabilidad calibrada, contactar, beneficio esperado, 3 razones SHAP), `POST /predict/batch` (≤ 1.000), `POST /explain`. Contrato Pydantic con campos extra prohibidos: `Gender` o IDs → **422**.
- **Modelo por GitHub Release:** tag `model-v1.0`, archivo `model.joblib`, SHA-256 `579b7fe349dc035c3171582cbfba1bfaed4599a795da4b149d7664ed21dc095a`. `artifact.py` descarga y **falla si el hash no coincide** (build y arranque).
- **LLM opcional** (`narrative.py`): compatible con OpenAI vía `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` (NVIDIA NIM `https://integrate.api.nvidia.com/v1` u OpenRouter `https://openrouter.ai/api/v1`). Sin clave o con error → plantilla. Nunca envía IDs ni `Gender`. La clave va en `.env` (no versionado) o en secretos del Space.
- **Docker:** una imagen (`ROLE=api|dashboard|all`); compose con API en 8000 y dashboard en 8501. En Spaces (`ROLE=all`) el dashboard usa el puerto 7860.
- Verificado en Docker Desktop (Windows) con `verify-docker.ps1 -LocalModel` (modelo local, mismo SHA-256). Defecto corregido: `httpx` faltaba en runtime (`1b300a2`); `tests/test_packaging.py` lo vigila.

## 7. Pendientes inmediatos (en orden)

1. `git push origin main` (el repo local va **13 commits** por delante).
2. **Publicar el Release** (aún no existe): https://github.com/darwinjaco/bank-churn-ml/releases/new → tag `model-v1.0` (*Create new tag*) → adjuntar `models\model.joblib` → *Publish release*.
3. Con el Release publicado: `pwsh -File scripts/verify-docker.ps1` (variante por defecto, la que usará Hugging Face). Con `-LocalModel` ya pasó.
4. Si todo pasa: marcar en spec 005 y registro (S11) el criterio `docker compose up`, y revisar el CI.
5. `uv sync --locked --all-groups` en Windows (faltan `xgboost-cpu`, `shap`, `fastapi`, etc. en el `.venv`).

## 8. Semana 8 (siguiente)

- Spec 006 primero (T0). Desplegar en **Hugging Face Spaces (Docker)**, una sola URL; secretos LLM en el Space.
- Drift simulado con Evidently (se recorta primero si falta tiempo).
- README final de portafolio: resumen en inglés al inicio, GIF de demo, enlace público.
- Trabajo futuro registrado: opciones B (presupuesto/deciles) y C (sensibilidad) de la spec 004; mitigación de E-01; migrar `penalty="l2"` (obsoleto en scikit-learn 1.10).

## 9. Notas técnicas para quien retome

- Windows: `uv` gestiona `.venv`; `.gitattributes` fuerza LF. No ejecutar `uv` desde otro sistema operativo sobre el `.venv` de Windows.
- Comprobaciones locales: `uv sync --locked --all-groups`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run pre-commit run --all-files`, `uv run pytest --cov=churn --cov-fail-under=85`. Último resultado: 194 tests, 98 % de cobertura.
- MLflow: `uv run mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db` (base local, fuera de Git).
- La reproducción completa desde un clon limpio da resultados idénticos a los versionados (verificado antes de la semana 6).
- Commits con autor `Darwin Jacome <daabjaco@espol.edu.ec>` y línea `Co-Authored-By` de Claude cuando corresponde.
