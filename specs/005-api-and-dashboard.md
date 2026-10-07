# Especificación 005 — API y dashboard

| Campo | Valor |
|---|---|
| Estado | Aprobada v1.0 |
| Responsable | Darwin Jacome Cuenca |
| Semana | 7 (16–22 de noviembre de 2026) |
| Dependencias | [002](002-modeling-and-evaluation.md) (artefacto congelado), [004](004-decision-layer.md) (regla de decisión) |

## 1. Objetivo

Servir el modelo congelado como una API y un dashboard reproducibles con un solo comando, sin reentrenar y sin el CSV, para que cualquier persona pueda probar la decisión de retención.

## 2. Arquitectura

```text
Navegador ──▶ Streamlit (dashboard) ──HTTP──▶ FastAPI ──▶ CalibratedModel + SHAP
                                                   └──▶ (opcional) LLM compatible con OpenAI
```

- El dashboard **no carga el modelo**: toda predicción pasa por la API.
- Local: `docker compose up` levanta dos servicios (`api`, `dashboard`).
- Hugging Face Spaces (semana 8): una sola imagen que arranca ambos procesos; el dashboard escucha en el puerto público 7860 y la API en `localhost:8000`.

## 3. Distribución del modelo

- El artefacto `model.joblib` se publica como asset de un **GitHub Release** (`model-v1.0`) del repositorio.
- `artifact.py` fija la URL y el SHA-256 esperado (`579b7fe3…095a`). `ensure_model()` descarga el archivo si falta y **falla si el hash no coincide**; la API verifica el hash otra vez al arrancar.
- La metadata se lee de `reports/model_metadata.json` (versionada). El CSV nunca entra en la imagen.

## 4. Endpoints

| Método y ruta | Entrada | Salida |
|---|---|---|
| `GET /health` | — | `status`, SHA-256 del artefacto, commit del modelo |
| `GET /model` | — | Variables, calibrador, umbral, supuestos y métricas de la evaluación final |
| `POST /predict` | Un cliente | `churn_probability` (calibrada), `contact` (bool), `expected_benefit_eur`, `threshold`, `top_reasons` (3 contribuciones SHAP con signo) |
| `POST /predict/batch` | Lista de 1 a 1.000 clientes | Lista de predicciones (sin razones) y resumen: contactados y beneficio esperado total |
| `POST /explain` | Un cliente | Texto breve en español con la recomendación y sus razones; `source` = `llm` o `template` |

## 5. Contrato de entrada (Pydantic)

Mismos rangos que el contrato de datos (spec 001): `CreditScore` 300–900, `Age` 18–100, `Tenure` 0–10, `Balance` ≥ 0, `NumOfProducts` 1–4, `HasCrCard` y `IsActiveMember` ∈ {0, 1}, `Geography` ∈ {France, Germany, Spain}. `EstimatedSalary` es opcional y se ignora (excluida por E-03). **Campos extra prohibidos**: un `Gender` o un identificador devuelve 422.

## 6. Reglas

- Umbral, supuestos y calibrador salen de la metadata, no se escriben en la API.
- El modelo y el explicador SHAP se cargan una vez al arrancar.
- Las razones SHAP explican la probabilidad sin calibrar (spec 002 §11.1); se presentan como factores del modelo, no como causas.
- **LLM opcional** (`/explain`): cliente compatible con OpenAI configurado por `LLM_BASE_URL`, `LLM_API_KEY` y `LLM_MODEL` (por ejemplo, NVIDIA NIM u OpenRouter). Solo recibe las variables del cliente, la probabilidad, la decisión y las razones SHAP: nunca identificadores. Sin clave, con error o con tiempo de espera superado (10 s), se usa una plantilla determinista. La clave vive solo en variables de entorno o secretos del Space, nunca en el repositorio.
- Sin autenticación ni límite de uso: es una demo de portafolio (limitación documentada).

## 7. Dashboard

1. **Cliente individual:** formulario → probabilidad, decisión, beneficio esperado, razones y explicación textual.
2. **Lote:** subir un CSV con las columnas del contrato → tabla con decisiones y resumen (contactados, beneficio esperado), descargable.
3. **Modelo:** métricas de la evaluación final, supuestos y enlace a la ficha del modelo.

## 8. Tests

- `TestClient`: `/health`, `/model`, `/predict` con la misma probabilidad que el artefacto, 422 por rango inválido, categoría desconocida y campo `Gender`, lote vacío o con más de 1.000 filas.
- `artifact.py`: descarga simulada, hash correcto e incorrecto.
- LLM: cliente simulado; sin clave → plantilla; error → plantilla; nunca se envían identificadores.
- Dashboard: funciones de formato puras con tests; la interfaz se prueba manualmente.
- Docker: `docker compose up` desde cero y una petición real a `/predict` (verificación manual registrada).

## 9. Criterios de aceptación

- [ ] `docker compose up` levanta API y dashboard desde un clon limpio (con el Release publicado).
- [ ] `/predict` devuelve la misma probabilidad que `models/model.joblib` para el mismo cliente.
- [ ] Hash del artefacto verificado en build y al arrancar.
- [ ] Sin clave de LLM, `/explain` responde con la plantilla.
- [ ] CI en verde con cobertura ≥ 85 %.
