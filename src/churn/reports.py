"""Reportes legibles y diferencias pareadas, sin ajustar modelos."""

from __future__ import annotations

import json

import numpy as np

from churn.config import PROJECT_ROOT

METRICS = ("ap", "roc_auc", "brier", "log_loss")
BASELINES_JSON = PROJECT_ROOT / "reports" / "baselines.json"
BASELINES_MD = PROJECT_ROOT / "reports" / "baselines.md"


def paired_differences(reference: list[dict], candidate: list[dict], metric: str = "ap") -> dict:
    """Diferencias candidato menos referencia sobre los mismos pliegues."""
    left = sorted(reference, key=lambda fold: fold["fold"])
    right = sorted(candidate, key=lambda fold: fold["fold"])
    if len(left) != len(right) or len(left) < 2:
        raise ValueError("Se requieren al menos dos pliegues pareados de igual longitud.")
    differences = []
    for a, b in zip(left, right, strict=True):
        if any(
            a.get(key) != b.get(key)
            for key in ("fold", "fit_indices_sha256", "score_indices_sha256")
        ):
            raise ValueError("Los pliegues no coinciden.")
        differences.append(float(b["metrics"][metric] - a["metrics"][metric]))
    return {
        "by_fold": differences,
        "mean": float(np.mean(differences)),
        "std": float(np.std(differences, ddof=1)),
        "positive": sum(value > 0 for value in differences),
        "negative": sum(value < 0 for value in differences),
        "zero": sum(value == 0 for value in differences),
    }


def metric_table(runs: list[dict], name_key: str = "name") -> str:
    rows = ["| Modelo | AP | ROC-AUC | Brier | Log loss |", "|---|---|---|---|---|"]
    for run in runs:
        values = [
            f"{run['summary'][metric]['mean']:.3f} ± {run['summary'][metric]['std']:.3f}"
            for metric in METRICS
        ]
        rows.append("| " + run[name_key] + " | " + " | ".join(values) + " |")
    return "\n".join(rows)


def render_baselines(data: dict) -> str:
    runs = {run["name"]: run for run in data["runs"]}
    paired = paired_differences(runs["logreg-raw"]["folds"], runs["logreg-eda"]["folds"])
    rows = ["| Pliegue | Δ AP EDA - RAW | Signo |", "|---|---|---|"]
    for number, difference in enumerate(paired["by_fold"], start=1):
        sign = "positivo" if difference > 0 else "negativo" if difference < 0 else "cero"
        rows.append(f"| {number} | {difference:+.3f} | {sign} |")
    identifiers = [f"| {run['name']} | `{run['run_id']}` |" for run in data["runs"]]
    return (
        "\n\n".join(
            [
                "# Baselines — Semana 3",
                (
                    "Fuente: [baselines.json](baselines.json); reporte generado con "
                    "`uv run python -m churn.reports`."
                ),
                (
                    f"CV de entrenamiento: **{data['n_training']:,} filas**, "
                    f"{data['n_folds']} pliegues estratificados, shuffle=True "
                    f"y semilla {data['seed']}. "
                    "Media ± desviación estándar muestral (ddof=1). AP es precisión promedio; "
                    "tablas legibles a tres decimales."
                ),
                (
                    "Configuraciones históricas fijas de semana 3: Dummy prior y LogReg L2, C=1, "
                    "lbfgs, max_iter=1000; sin ponderación ni remuestreo. FS-RAW/FS-EDA según "
                    "la spec 002. Validación externa y prueba reservadas."
                ),
                "## Tabla generada desde JSON",
                metric_table(data["runs"]),
                "## Diferencia pareada de AP por pliegue",
                "\n".join(rows),
                (
                    f"Δ AP EDA - RAW: **{paired['mean']:+.3f} ± {paired['std']:.3f}**; "
                    f"{paired['positive']}/{len(paired['by_fold'])} positivos. La desviación "
                    "corresponde a las diferencias pareadas, no a las desviaciones de cada modelo "
                    "por separado."
                ),
                "## Lectura descriptiva",
                (
                    "- Dummy tiene AP acorde con la prevalencia de entrenamiento y ROC-AUC 0,500 "
                    "como referencia mínima.\n- Las diferencias pareadas muestran "
                    "el signo en cada pliegue; no constituyen una prueba de significación.\n"
                    "- La tabla conserva ROC-AUC, Brier y log loss de las configuraciones "
                    "fijadas previamente.\n- Estas métricas son de desarrollo; la regla de "
                    "selección de semana 4 se aplica a su reevaluación preregistrada."
                ),
                "## Trazabilidad MLflow local",
                (
                    "Tracking: `sqlite:///mlruns/mlflow.db`; experimento `bank-churn`. "
                    "Todas las corridas tienen stage=baseline y final=false; Dummy eligible=false. "
                    "Base local excluida de Git."
                ),
                "| Corrida | Run ID |\n|---|---|\n" + "\n".join(identifiers),
                (
                    f"Código registrado: `{data['git_commit']}`. "
                    f"CSV SHA-256: `{data['csv_sha256']}`. "
                    f"Manifiesto SHA-256 consumido: `{data['split_manifest_sha256']}`."
                ),
                (
                    "```powershell\nuv run mlflow ui --backend-store-uri "
                    "sqlite:///mlruns/mlflow.db --port 5000\n```\n\n"
                    "Interfaz: http://127.0.0.1:5000. "
                    "Reproducir: `uv sync --locked --all-groups` y `uv run churn-baselines`; "
                    "crearán nuevas corridas con la misma configuración."
                ),
            ]
        )
        + "\n"
    )


def main() -> int:
    data = json.loads(BASELINES_JSON.read_text(encoding="utf-8"))
    BASELINES_MD.write_text(render_baselines(data), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
