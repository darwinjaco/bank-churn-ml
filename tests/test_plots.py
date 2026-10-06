"""Verifica la generación headless y los límites de los entregables gráficos."""

import json

import pandas as pd
import pytest

from churn import plots
from churn.config import AGE_LABELS


@pytest.fixture
def plot_input():
    def rates(levels):
        return {
            level: {"n": 40, "k": 8, "rate": 0.2, "ic_low": 0.1, "ic_high": 0.3} for level in levels
        }

    results = [
        {"id": "H1", "detalles": {"rates": rates(("0", "1"))}},
        {"id": "H2", "detalles": {"rates": rates(("1", "2", "3-4"))}},
        {
            "id": "H3",
            "detalles": {
                "or_crudo": {"estimate": 2.0, "ic_low": 1.5, "ic_high": 2.5},
                "or_ajustado": {"estimate": 1.5, "ic_low": 1.1, "ic_high": 1.9},
            },
        },
        {"id": "H4", "detalles": {"rates": rates(AGE_LABELS)}},
        {"id": "H5", "detalles": {"rates": rates(("0", "1"))}},
    ]
    df = pd.DataFrame(
        {"Balance": [0.0, 10000.0, 20000.0] * 10, "EstimatedSalary": list(range(1000, 4000, 100))}
    )
    return df, results


def test_six_valid_png_under_size_limit(plot_input, tmp_path):
    df, results = plot_input
    paths = plots.generate_figures(df, results, tmp_path)
    assert len(paths) == 6
    assert len(set(paths)) == 6
    assert all(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for path in paths)
    assert all(0 < path.stat().st_size < 200_000 for path in paths)
    assert not plots.plt.get_fignums()


def test_main_reads_results_and_exploration(plot_input, monkeypatch, tmp_path):
    df, results = plot_input
    report = tmp_path / "hypotheses.json"
    report.write_text(json.dumps(results), encoding="utf-8")
    monkeypatch.setattr(plots, "HYPOTHESES_FILE", report)
    monkeypatch.setattr(plots, "FIGURES_DIR", tmp_path / "figures")
    monkeypatch.setattr(plots, "load_exploration", lambda: df)
    assert plots.main() == 0
    assert len(list(plots.FIGURES_DIR.glob("*.png"))) == 6
