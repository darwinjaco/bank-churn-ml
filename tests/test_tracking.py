"""Procedencia: hash canónico del manifiesto (spec 002 v1.5)."""

import hashlib
import json

from churn import tracking


def test_manifest_hash_ignores_line_endings_and_key_order(tmp_path):
    content = {"seed": 42, "partitions": {"test": {"n_rows": 2000}}, "csv_sha256": "x"}
    lf = tmp_path / "lf.json"
    crlf = tmp_path / "crlf.json"
    reordered = tmp_path / "reordered.json"
    lf.write_bytes(json.dumps(content, indent=2).encode())
    crlf.write_bytes(json.dumps(content, indent=2).replace("\n", "\r\n").encode())
    reordered.write_text(json.dumps(dict(reversed(content.items()))), encoding="utf-8")
    assert lf.read_bytes() != crlf.read_bytes()
    digest = tracking.manifest_sha256(lf)
    assert digest == tracking.manifest_sha256(crlf) == tracking.manifest_sha256(reordered)
    changed = tmp_path / "changed.json"
    changed.write_text(json.dumps({**content, "seed": 43}), encoding="utf-8")
    assert tracking.manifest_sha256(changed) != digest
    assert digest != hashlib.sha256(lf.read_bytes()).hexdigest()


def test_provenance_uses_canonical_hash():
    origin = tracking.provenance()
    assert len(origin["git_commit"]) == 40 and len(origin["csv_sha256"]) == 64
    assert origin["split_manifest_sha256"] == tracking.manifest_sha256()
