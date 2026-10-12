"""Informe mínimo de Gitleaks: nunca conserva texto ni valores detectados (spec 007 §9)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def minimize_findings(payload, scanner_exit: int) -> tuple[dict, int]:
    if not isinstance(payload, list) or any(not isinstance(row, dict) for row in payload):
        return {"status": "error", "reason": "Informe de escáner no válido"}, 2
    findings = []
    for row in payload:
        if not all(isinstance(row.get(key), str) for key in ("RuleID", "File", "Commit")):
            return {"status": "error", "reason": "Metadatos de hallazgo incompletos"}, 2
        if not isinstance(row.get("StartLine"), int):
            return {"status": "error", "reason": "Ubicación de hallazgo no válida"}, 2
        findings.append(
            {
                "rule": row["RuleID"],
                "file": row["File"],
                "line": row["StartLine"],
                "commit": row["Commit"],
            }
        )
    if scanner_exit not in (0, 1) or (scanner_exit == 1 and not findings):
        return {"status": "error", "reason": "El escáner no completó un análisis satisfactorio"}, 2
    return {
        "status": "findings" if findings else "passed",
        "count": len(findings),
        "findings": findings,
    }, 1 if findings else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--exit-code", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.raw.read_text(encoding="utf-8"))
        report, code = minimize_findings(payload, args.exit_code)
    except (OSError, ValueError):
        report, code = {"status": "error", "reason": "Informe ausente o ilegible"}, 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"Escaneo de secretos: {report['status']}; hallazgos={report.get('count', 'desconocido')}"
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
