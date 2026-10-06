# Baselines — Semana 3

Fuente: [baselines.json](baselines.json); reporte generado con `uv run python -m churn.reports`.

CV de entrenamiento: **6,000 filas**, 5 pliegues estratificados, shuffle=True y semilla 42. Media ± desviación estándar muestral (ddof=1). AP es precisión promedio; tablas legibles a tres decimales.

Configuraciones históricas fijas de semana 3: Dummy prior y LogReg L2, C=1, lbfgs, max_iter=1000; sin ponderación ni remuestreo. FS-RAW/FS-EDA según la spec 002. Validación externa y prueba reservadas.

## Tabla generada desde JSON

| Modelo | AP | ROC-AUC | Brier | Log loss |
|---|---|---|---|---|
| dummy-raw | 0.204 ± 0.000 | 0.500 ± 0.000 | 0.162 ± 0.000 | 0.506 ± 0.001 |
| logreg-raw | 0.459 ± 0.029 | 0.755 ± 0.012 | 0.138 ± 0.004 | 0.435 ± 0.009 |
| logreg-eda | 0.657 ± 0.028 | 0.839 ± 0.021 | 0.111 ± 0.005 | 0.364 ± 0.018 |

## Diferencia pareada de AP por pliegue

| Pliegue | Δ AP EDA - RAW | Signo |
|---|---|---|
| 1 | +0.178 | positivo |
| 2 | +0.230 | positivo |
| 3 | +0.193 | positivo |
| 4 | +0.193 | positivo |
| 5 | +0.194 | positivo |

Δ AP EDA - RAW: **+0.198 ± 0.019**; 5/5 positivos. La desviación corresponde a las diferencias pareadas, no a las desviaciones de cada modelo por separado.

## Lectura descriptiva

- Dummy tiene AP acorde con la prevalencia de entrenamiento y ROC-AUC 0,500 como referencia mínima.
- Las diferencias pareadas muestran el signo en cada pliegue; no constituyen una prueba de significación.
- La tabla conserva ROC-AUC, Brier y log loss de las configuraciones fijadas previamente.
- Estas métricas son de desarrollo; la regla de selección de semana 4 se aplica a su reevaluación preregistrada.

## Trazabilidad MLflow local

Tracking: `sqlite:///mlruns/mlflow.db`; experimento `bank-churn`. Todas las corridas tienen stage=baseline y final=false; Dummy eligible=false. Base local excluida de Git.

| Corrida | Run ID |
|---|---|
| dummy-raw | `67f346cabc794a749c709d298a8a77d8` |
| logreg-raw | `22b313957b96480bbd21f50a4130b1df` |
| logreg-eda | `bef5ae63e7b8421abcfee5f1ad65dd5c` |

Código registrado: `c75af93fbfb0dd87f51efeb39fa70071caa4d399`. CSV SHA-256: `3996cd1fa372e0db0cd9c0ebac35bbd4e8e3c65fb942bb010c826e7b1eeef0a0`. Manifiesto SHA-256 consumido: `978161d49e6b6394b8550beeb49dc93b20ce467a2ac2b810033b370f713827f8`.

```powershell
uv run mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db --port 5000
```

Interfaz: http://127.0.0.1:5000. Reproducir: `uv sync --locked --all-groups` y `uv run churn-baselines`; crearán nuevas corridas con la misma configuración.
