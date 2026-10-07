# Contexto del proyecto — bank-churn-ml (documento de cierre)

Documento de traspaso para quien retome el proyecto (persona o agente). Estado al **7 de octubre de 2026**: semanas 1–8 implementadas; quedan acciones externas del responsable (§6). Base de código: `30c0809` más los cambios de la semana 8.

## 1. Qué es

Proyecto de portafolio de Darwin Jacome Cuenca: **predicción de abandono bancario convertida en decisiones de retención**. Calcula a quién conviene contactar y cuánto dinero aporta frente a no usar modelo, bajo supuestos económicos explícitos.

- Repositorio: https://github.com/darwinjaco/bank-churn-ml (rama `main`, público).
- Demo prevista: https://huggingface.co/spaces/darwinjaco/bank-churn-ml (usuario provisional, B-03).
- Dataset: *Churn Modelling* (Kaggle), 10.000 clientes, probablemente sintético. El CSV **no** se versiona (`data/raw/Churn_Modelling.csv`).
- Idioma: español (identificadores técnicos en inglés); resumen del README en inglés.

## 2. Forma de trabajo (obligatoria)

- **SDD:** ninguna línea de `src/` o `tests/` sin spec y plan versionados. Cada semana empieza con una tarea T0 de documentación.
- **Una tarea = un commit**, con el mensaje fijado en el plan; Ruff, formato, hooks y pytest (≥ 85 %) en verde.
- **Preregistro:** hipótesis, reglas, umbrales y expectativas antes de ver resultados; los cambios son enmiendas versionadas.
- **Reglas fijas (`AGENTS.md`):** `Gender` nunca es variable del modelo (solo auditoría); la partición de prueba ya se usó **una vez** y no se vuelve a evaluar (tampoco para monitoreo); el modelo `model-v1.0` está congelado.
- **Registro:** `docs/registro-avance.md` (S01–S12, estado y Definition of Done en §6). Todas las cifras de reportes se generan desde JSON con código.
- Desde la semana 4, Claude planifica, implementa y verifica; en la semana 8 el responsable hace los commits al final.

## 3. Estado por semana

| Semana | Contenido | Estado |
|---|---|---|
| 1–6 | Contrato, división, EDA, pipelines, ajuste, calibración, decisión, SHAP, auditoría y evaluación final en prueba | Cerradas y publicadas (CI #29 en `6e8e54d`) |
| 7 | API FastAPI, dashboard Streamlit, Docker, LLM opcional | Implementada; Docker verificado con modelo local; falta repetir con el Release |
| 8 | Sincronización con Hugging Face, límite del LLM, monitoreo simulado, README final, revisión de código | Implementada y verificada en local; despliegue pendiente (B-03) |

## 4. Resultados clave

- **Modelo final:** Random Forest (500 árboles, `max_depth` 10, `min_samples_leaf` 5, `max_features` sqrt), sin `EstimatedSalary` (E-03), calibración **sigmoide** (E-04). Elegido sobre XGBoost por parsimonia (0,011 < 0,018).
- **Regla:** contactar si p > t\* = c / (s·V) = 50 / (0,30 · 1.000) = **1/6**.
- **Prueba (única, 7 oct 2026):** AP 0,705, ROC-AUC 0,862, Brier 0,1017. Contacta a 634 de 2.000 y obtiene **61.600 €** frente a 22.100 € contactando a todos (60,5 % del oráculo); precisión 49,1 %, sensibilidad 76,4 %.
- **Auditoría:** SHAP → Age, NumOfProducts, IsActiveMember, Germany. Abandonos no detectados: jóvenes y activos. E-01: igual tasa de contacto y sensibilidad por género; alerta en precisión (59,6 % frente a 42,2 %).
- **Monitoreo (spec 006):** E1, E3 y E4 cumplidas; E2 no (S3, PSI 0,196, anticipado). Lección: el cambio de prevalencia (S4) descalibra −9,6 pp sin alarmas de PSI.

## 5. Estructura

```text
specs/        001 contrato · 002 modelado (v1.6) · 003 EDA (v1.1) · 004 decisión · 005 API (v1.1) · 006 despliegue y monitoreo
docs/         registro-avance.md, plan-semana-2..8.md, historial-semanal.md, este archivo
src/churn/    config, data, validation, split, stats, hypotheses, features, pipeline, train, tune, selection,
              experiments, calibration, decision, decide, explain, audit, run_audit, final_eval, model_card,
              artifact, api, narrative, ui, monitoring, plots, reports, tracking
dashboard/    app.py (Streamlit; solo consume la API)
reports/      JSON y Markdown generados (incluido monitoring) y figures/
scripts/      verify-docker.ps1, build_space.py, make_example_csv.py
deploy/space/ README del Space · examples/ CSV sintético · .github/workflows/ ci.yml y deploy-space.yml
models/       model.joblib (16 MB, fuera de Git; Release model-v1.0, SHA-256 579b7fe3…095a) + metadata.json
```

CLIs: `churn-validate`, `churn-split`, `churn-hypotheses`, `churn-baselines`, `churn-tune`, `churn-select`, `churn-decide`, `churn-audit`, `churn-monitor` y `churn-final` (ya ejecutado: falla si se repite).

## 6. Pendientes (responsable, en orden)

1. Commits de la semana 8 (plan en `docs/plan-semana-8.md`), `git push origin main` y CI en verde.
2. Release `model-v1.0` con `models/model.joblib`.
3. `pwsh -File scripts/verify-docker.ps1` sin `-LocalModel` (incluye la imagen del Space).
4. Cuenta y token de Hugging Face (B-03); crear el Space (Docker, *Blank*, público); `HF_TOKEN` (secreto) y `HF_SPACE` (variable) en GitHub.
5. *Actions → Deploy Space → Run workflow*; verificar la URL pública con el cliente de referencia (0,947, contactar); secretos del LLM en el Space.
6. GIF de demo y etiqueta/Release `v1.0.0`; marcar los criterios restantes de las specs 005 y 006.

## 7. Notas técnicas

- Windows: `uv` gestiona `.venv`; `.gitattributes` fuerza LF. No ejecutar `uv` desde otro sistema operativo sobre el `.venv` de Windows (la verificación de Claude usa un entorno aparte).
- Comprobaciones: `uv sync --locked --all-groups`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run pre-commit run --all-files`, `uv run pytest --cov=churn --cov-fail-under=85`. Último resultado: 243 tests, 98,25 % (240 + 3 omitidos sin datos en un clon limpio).
- MLflow: `uv run mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db` (local, fuera de Git).
- LLM opcional: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` y `LLM_MAX_CALLS_PER_HOUR` (vacío = 30) en `.env` o secretos del Space.
- Trabajo futuro: opciones B y C de la spec 004, mitigación de E-01, uplift, monitoreo con etiquetas reales, migrar `penalty="l2"` (obsoleto en scikit-learn 1.10).
- Commits con autor `Darwin Jacome <daabjaco@espol.edu.ec>` y línea `Co-Authored-By` de Claude cuando corresponde.
