"""Descarga y verificación del artefacto sin red (descargador simulado)."""

import hashlib

import joblib
import pytest

from churn import artifact


def _fake(content: bytes):
    calls = []

    def downloader(url, destination):
        calls.append(url)
        destination.write_bytes(content)

    return downloader, calls


def test_downloads_verifies_and_reuses(tmp_path):
    content = b"modelo-de-prueba"
    expected = hashlib.sha256(content).hexdigest()
    downloader, calls = _fake(content)
    path = tmp_path / "models" / "model.joblib"
    assert artifact.ensure_model(path, "https://x/model.joblib", expected, downloader) == path
    assert path.read_bytes() == content and calls == ["https://x/model.joblib"]
    artifact.ensure_model(path, "https://x/model.joblib", expected, downloader)
    assert len(calls) == 1  # Ya existe y es válido: no vuelve a descargar.
    assert not list(path.parent.glob("*.part"))


def test_bad_download_is_rejected_and_not_kept(tmp_path):
    downloader, _ = _fake(b"alterado")
    path = tmp_path / "model.joblib"
    with pytest.raises(artifact.ArtifactIntegrityError):
        artifact.ensure_model(path, "https://x", "0" * 64, downloader)
    assert not path.exists() and not list(tmp_path.glob("*.part"))


def test_existing_file_with_wrong_hash_fails(tmp_path):
    path = tmp_path / "model.joblib"
    path.write_bytes(b"otro")
    with pytest.raises(artifact.ArtifactIntegrityError):
        artifact.ensure_model(path, "https://x", "0" * 64, _fake(b"")[0])


def test_load_model_and_env_override(tmp_path, monkeypatch):
    path = tmp_path / "m.joblib"
    joblib.dump({"ok": True}, path)
    expected = artifact.sha256_file(path)
    assert artifact.load_model(path, expected) == {"ok": True}
    monkeypatch.setenv("MODEL_PATH", str(path))
    assert artifact.model_path() == path


def test_published_hash_matches_local_artifact_when_present():
    if not artifact.DEFAULT_MODEL_PATH.exists():
        pytest.skip("Artefacto local ausente (esperado en CI).")
    assert artifact.sha256_file(artifact.DEFAULT_MODEL_PATH) == artifact.MODEL_SHA256
