"""El helper no entrega credenciales a otro host, Space o protocolo."""

import io

import pytest
from scripts import hf_credentials

ENV = {"HF_SPACE": "demo/bank-churn-ml", "HF_TOKEN": "credencial-sintetica"}
CONTEXT = {"protocol": "https", "host": "huggingface.co", "path": "spaces/demo/bank-churn-ml"}


@pytest.mark.parametrize(
    "change",
    [{"host": "otro.invalid"}, {"protocol": "http"}, {"path": "spaces/otro/modelo"}],
)
def test_credentials_are_scoped(change):
    assert hf_credentials.credential({**CONTEXT, **change}, ENV) == {}
    assert hf_credentials.credential(CONTEXT, ENV)["password"] == ENV["HF_TOKEN"]


@pytest.mark.parametrize("change", [{"HF_TOKEN": ""}, {"HF_TOKEN": "x\ny"}, {"HF_SPACE": "../x"}])
def test_invalid_secret_or_space_is_rejected(change):
    assert hf_credentials.credential(CONTEXT, {**ENV, **change}) == {}


def test_helper_uses_only_credential_protocol(monkeypatch, capsys):
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(
        hf_credentials.sys,
        "stdin",
        io.StringIO("protocol=https\nhost=huggingface.co\npath=spaces/demo/bank-churn-ml\n\n"),
    )
    assert hf_credentials.main(["get"]) == 0
    assert capsys.readouterr().out == "username=hf\npassword=credencial-sintetica\n"
    assert hf_credentials.main(["store"]) == 0
    assert capsys.readouterr().out == ""
