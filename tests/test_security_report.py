"""El informe no filtra el secreto ni convierte errores/informes ausentes en verde."""

import json

import pytest
from scripts import security_report


def test_report_exposes_only_location_even_if_scanner_has_unredacted_data():
    raw = [
        {
            "RuleID": "test-rule",
            "File": "config.py",
            "StartLine": 10,
            "Commit": "a" * 40,
            "Secret": "dato-confidencial",
            "Match": "dato-confidencial",
            "Line": "dato-confidencial",
            "Author": "persona",
            "Message": "dato-confidencial",
        }
    ]
    report, code = security_report.minimize_findings(raw, 1)
    assert code == 1 and report["count"] == 1
    assert report["findings"] == [
        {"rule": "test-rule", "file": "config.py", "line": 10, "commit": "a" * 40}
    ]
    assert "dato-confidencial" not in json.dumps(report)
    assert "persona" not in json.dumps(report)
    assert security_report.minimize_findings(raw, 0)[1] == 1


@pytest.mark.parametrize(
    "payload, status",
    [
        ([], 1),
        ([], 2),
        ({}, 0),
        ([None], 0),
        ([{}], 1),
        ([{"RuleID": "x", "File": "x", "Commit": "x"}], 1),
    ],
)
def test_bad_scan_or_bad_report_fails(payload, status):
    report, code = security_report.minimize_findings(payload, status)
    assert code != 0 and report["status"] == "error"


def test_cli_missing_report_is_not_a_success(tmp_path, capsys):
    output = tmp_path / "safe.json"
    assert (
        security_report.main([str(tmp_path / "missing.json"), str(output), "--exit-code", "0"]) == 2
    )
    assert json.loads(output.read_text())["status"] == "error"
    raw = tmp_path / "raw.json"
    raw.write_text("[]")
    assert security_report.main([str(raw), str(output), "--exit-code", "0"]) == 0
    assert json.loads(output.read_text())["status"] == "passed"
    assert "Escaneo de secretos" in capsys.readouterr().out
