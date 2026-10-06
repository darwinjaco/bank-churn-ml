# Baselines — Semana 3

Fuente: [baselines.json](baselines.json), generado por `uv run churn-baselines` con la especificación 002 v1.1.

- Exclusivamente **6.000 filas de entrenamiento**, cinco pliegues estratificados con mezcla y semilla 42; los hashes de índices de cada pliegue coinciden entre las tres corridas.
- AP corresponde a precisión promedio (`average_precision_score`). Las celdas muestran **media ± desviación estándar muestral**, con `ddof=1` entre los cinco pliegues.
- Configuración fija: Dummy con estrategia prior; LogReg L2, C=1, lbfgs y max_iter=1000. FS-RAW y FS-EDA según §3; sin remuestreo ni ponderación de clases.
- Evaluación de desarrollo en CV de entrenamiento; selección reservada para semana 4. Validación y prueba no se utilizan para las métricas de esta semana.

## Tabla generada desde JSON

| Modelo | AP | ROC-AUC | Brier | Log loss |
|---|---|---|---|---|
| dummy-raw | 0.203833 ± 0.000456 | 0.500000 ± 0.000000 | 0.162285 ± 0.000270 | 0.505671 ± 0.000622 |
| logreg-raw | 0.459104 ± 0.029316 | 0.755001 ± 0.012016 | 0.137894 ± 0.003545 | 0.435357 ± 0.009273 |
| logreg-eda | 0.656790 ± 0.028053 | 0.839331 ± 0.021047 | 0.110680 ± 0.004947 | 0.364184 ± 0.018428 |

Código utilizado para generar las filas, sin recalcular ni introducir resultados manuales:

```python
import json

from churn.config import PROJECT_ROOT

data = json.loads((PROJECT_ROOT / "reports/baselines.json").read_text(encoding="utf-8"))
metrics = ("ap", "roc_auc", "brier", "log_loss")
print("| Modelo | AP | ROC-AUC | Brier | Log loss |")
print("|---|---|---|---|---|")
for run in data["runs"]:
    values = [
        "{:.6f} ± {:.6f}".format(run["summary"][name]["mean"], run["summary"][name]["std"])
        for name in metrics
    ]
    print("| " + run["name"] + " | " + " | ".join(values) + " |")
```

## Trazabilidad MLflow local

Tracking URI: `sqlite:///mlruns/mlflow.db`, experimento `bank-churn`. Base y artefactos locales excluidos de Git; el JSON versionado conserva los identificadores y métricas. Todas las corridas tienen `stage=baseline` y `final=false`; Dummy tiene `eligible=false`.

| Corrida | Run ID |
|---|---|
| dummy-raw | `67f346cabc794a749c709d298a8a77d8` |
| logreg-raw | `22b313957b96480bbd21f50a4130b1df` |
| logreg-eda | `bef5ae63e7b8421abcfee5f1ad65dd5c` |

Código registrado: `c75af93fbfb0dd87f51efeb39fa70071caa4d399`. CSV SHA-256: `3996cd1fa372e0db0cd9c0ebac35bbd4e8e3c65fb942bb010c826e7b1eeef0a0`. Manifiesto SHA-256 de la copia consumida: `978161d49e6b6394b8550beeb49dc93b20ce467a2ac2b810033b370f713827f8`.

Para consultar las corridas desde la raíz del proyecto:

```powershell
uv run mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db --port 5000
```

Abre `http://127.0.0.1:5000`. Para reproducir la ejecución: `uv sync --locked --all-groups` y `uv run churn-baselines`; se crearán tres nuevas corridas con la misma configuración.
