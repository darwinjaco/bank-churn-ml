# Contexto del proyecto — bank-churn-ml (documento de cierre)

Documento de traspaso para quien retome el proyecto (persona o agente). Estado al
**15 de octubre de 2026**: entrega **v1.0.1 completada**, código
**`9384e51`**, integrado y desplegado desde `main`. CI y Security scans verdes;
auditoría HTTPS y navegador públicos satisfactorios. Los pendientes del snapshot
S24 se cerraron en la Release. La ampliación documental actual añade una memoria
técnica LaTeX, sin cambiar implementación ni resultados; evidencia en S25.

## 1. Qué es

Proyecto de portafolio de Darwin Jacome Cuenca: **predicción de abandono bancario convertida en decisiones de retención**. Calcula a quién conviene contactar y cuánto dinero aporta frente a no usar modelo, bajo supuestos económicos explícitos.

- Repositorio: https://github.com/darwinjaco/bank-churn-ml (público).
- Demo: https://bank-churn-ml-ufa7.onrender.com/ (Render Free, acceso directo HTTPS).
- Hugging Face se conserva como alternativa manual, sin despliegue certificado.
- Dataset: *Churn Modelling* (Kaggle), 10.000 clientes, probablemente sintético. El CSV **no** se versiona (`data/raw/Churn_Modelling.csv`).
- Idioma: español (identificadores técnicos en inglés); resumen del README en inglés.

## 2. Forma de trabajo (obligatoria)

- **SDD:** ninguna línea de `src/` o `tests/` sin spec y plan versionados. Cada semana empieza con una tarea T0 de documentación.
- **Cierre consolidado:** el responsable solicita un único commit al terminar la
  limpieza y la documentación, con comprobaciones satisfactorias. Las compuertas
  SDD previas siguen siendo obligatorias si se modifica código, tests o dependencias.
- **Preregistro:** hipótesis, reglas, umbrales y expectativas antes de ver resultados; los cambios son enmiendas versionadas.
- **Reglas fijas (`AGENTS.md`):** `Gender` nunca es variable del modelo (solo auditoría); la partición de prueba ya se usó **una vez** y no se vuelve a evaluar (tampoco para monitoreo); el modelo `model-v1.0` está congelado.
- **Registro:** `docs/registro-avance.md` (S01–S25; estado y Definition of Done en §6).
  Los planes semanales y secciones anteriores conservan el historial; las cifras
  de los reportes se generan desde JSON con código.

## 3. Estado por semana

| Semana | Contenido | Estado |
|---|---|---|
| 1–6 | Contrato, división, EDA, pipelines, ajuste, calibración, decisión, SHAP, auditoría y evaluación final en prueba | Cerradas y publicadas (CI #29 en `6e8e54d`) |
| 7 | API FastAPI, dashboard Streamlit, Docker, LLM opcional | Publicada; Release/hash y rediseño comprobados; última suite local de código: 322 aprobados, 98,19 % |
| 8 | Monitoreo simulado, despliegue, README y cierre | Cerrada sobre Render y v1.0.1; HF alternativo manual; memoria documental posterior en S25 |

## 4. Resultados clave

- **Modelo final:** Random Forest (500 árboles, `max_depth` 10, `min_samples_leaf` 5, `max_features` sqrt), sin `EstimatedSalary` (E-03), calibración **sigmoide** (E-04). Elegido sobre XGBoost por parsimonia (0,011 < 0,018).
- **Regla:** contactar si p > t\* = c / (s·V) = 50 / (0,30 · 1.000) = **1/6**.
- **Prueba (única, 7 oct 2026):** AP 0,705, ROC-AUC 0,862, Brier 0,1017. Contacta a 634 de 2.000 y obtiene **61.600 €** frente a 22.100 € contactando a todos (60,5 % del oráculo); precisión 49,1 %, sensibilidad 76,4 %.
- **Auditoría:** SHAP → Age, NumOfProducts, IsActiveMember, Germany. Abandonos no detectados: jóvenes y activos. E-01: igual tasa de contacto y sensibilidad por género; alerta en precisión (59,6 % frente a 42,2 %).
- **Monitoreo (spec 006):** E1, E3 y E4 cumplidas; E2 no (S3, PSI 0,196, anticipado). Lección: el cambio de prevalencia (S4) descalibra −9,6 pp sin alarmas de PSI.

## 5. Estructura

```text
specs/        001 contrato · 002 modelado · 003 EDA · 004 decisión · 005 API y dashboard · 006 despliegue · 007 seguridad
docs/         registro vigente, contexto, planes históricos y de cierre, seguridad y demo
src/churn/    config, data, validation, split, stats, hypotheses, features, pipeline, train, tune, selection,
              experiments, calibration, decision, decide, explain, audit, run_audit, final_eval, model_card,
              artifact, api, narrative, ui, monitoring, plots, reports, tracking, security, presentation
dashboard/    app.py (solo consume la API) y serve.py (launcher público con cabeceras)
reports/      JSON y Markdown generados (incluido monitoring) y figures/
scripts/      comprobación Docker/HTTPS, armado HF, credenciales HF, escaneos y CSV sintético
deploy/space/ README alternativo HF · examples/ CSV sintético · .github/workflows/ CI, Security scans y HF manual
models/       model.joblib (16 MB, fuera de Git; Release model-v1.0, SHA-256 579b7fe3…095a) + metadata.json
```

CLIs: `churn-validate`, `churn-split`, `churn-hypotheses`, `churn-baselines`, `churn-tune`, `churn-select`, `churn-decide`, `churn-audit`, `churn-monitor` y `churn-final` (ya ejecutado: falla si se repite).

## 6. Cierre vigente

- `model-v1.0` está publicado: asset `model.joblib`, 16.544.282 bytes y digest
  SHA-256 fijado; no es un prerrequisito pendiente.
- Clon limpio de `bacb47b`: 319 aprobados y 3 omitidos esperados sin datos/modelo,
  cobertura 98,11 %; lock, lint, formato y hooks satisfactorios. Build del Release
  correcto, imagen `ROLE=all` comprobada bajo 512 MiB y 0,1 CPU. Evidencia en S23.
- Deploy Live de `9384e51` confirmado por el responsable y comprobado mediante
  auditoría HTTPS independiente, doce controles de navegador y subida 204/sin
  token 403. Plantilla determinista; LLM desactivado. El arranque en frío de
  Render Free puede mostrar Application loading sin implicar un deploy fallido.
- Integración completada por avance rápido hacia `main`, sin conflictos ni
  commits adicionales de fusión. Solo queda `main` local y remota. Evidencia en
  los PR
  [#2](https://github.com/darwinjaco/bank-churn-ml/pull/2) y
  [#1](https://github.com/darwinjaco/bank-churn-ml/pull/1).
- [Release v1.0.1](https://github.com/darwinjaco/bank-churn-ml/releases/tag/v1.0.1)
  publicada con informe JSON y evidencia final. Se preservaron `v1.0.0` y
  `model-v1.0`; no hay tareas obligatorias abiertas de la entrega acordada.
- Hugging Face es opcional: no se necesita cuenta/token para cerrar Render ni
  se habilita un LLM público para satisfacer criterios históricos del Space.
- `render-prep` se conserva como stash histórico revisado; contiene propuestas
  no incorporadas. No aplicarlo sobre la interfaz actual sin otra decisión SDD.

## 7. Notas técnicas

- Windows: `uv` gestiona `.venv`; `.gitattributes` fuerza LF. No ejecutar `uv` desde otro sistema operativo sobre el `.venv` de Windows (la verificación de Claude usa un entorno aparte).
- Comprobaciones obligatorias: los cinco comandos exactos de AGENTS §4; incluir
  los archivos nuevos en pre-commit. El grupo `eda` se instala con
  `uv sync --locked --all-groups` cuando se necesita trabajar con el notebook.
- MLflow: `uv run mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db` (local, fuera de Git).
- LLM opcional: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` y `LLM_MAX_CALLS_PER_HOUR` (vacío = 30) en `.env` o secretos del Space.
- Trabajo futuro: opciones B y C de la spec 004, mitigación de E-01, uplift, monitoreo con etiquetas reales, migrar `penalty="l2"` (obsoleto desde scikit-learn 1.9; se elimina en la 1.10).
- Limpieza: cachés regenerables y temporales propios al final; conservar modelo,
  datos y MLflow. La carpeta `.venv` es el entorno instalado, no un entregable Git.

## 8. Cómo orientarse en la documentación

| Documento | Función |
|---|---|
| `README.md` | Presentación, recorrido, resultados e instrucciones de uso |
| `latex/memoria-tecnica.tex`, `latex/README.md` | Memoria completa y compilación del PDF local |
| `contexto-proyecto.md` | Traspaso y decisiones vigentes |
| `registro-avance.md` | Evidencia cronológica y estado actual en §6 |
| `plan-cierre-release.md` | Secuencia y condiciones de la entrega consolidada |
| `seguridad-demo.md`, `verificacion-seguridad-publica.md` | Controles y procedimiento de comprobación |
| `plan-semana-2..8.md`, `historial-semanal.md` | Planificación y resultados históricos; no son pendientes vigentes |
| Otros planes y `verificacion-preproduccion.md` | Decisiones anteriores; aplicar las enmiendas y el registro posteriores |

El código y los reportes siguen vinculados a esos planes. Se conservan para no
perder trazabilidad ni romper referencias de las especificaciones.
