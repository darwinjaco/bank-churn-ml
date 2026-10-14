"""Integridad del transporte y cabeceras del dashboard (spec 007 v1.2)."""

import asyncio
import runpy
from pathlib import Path

import pytest
import streamlit as st
import yaml
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from churn.dashboard_security import SECURITY_HEADERS, DashboardHeaders

ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize("path,status", [("/", 200), ("/denied", 403), ("/missing", 404)])
def test_http_status_body_and_security_headers_are_preserved(path, status):
    async def ok(request):
        return PlainTextResponse("contenido", headers={"referrer-policy": "unsafe-url"})

    async def denied(request):
        return PlainTextResponse("rechazado", status_code=403)

    app = Starlette(
        routes=[Route("/", ok), Route("/denied", denied)], middleware=[Middleware(DashboardHeaders)]
    )
    with TestClient(app) as client:
        response = client.get(path)
    assert response.status_code == status
    assert response.text == {200: "contenido", 403: "rechazado", 404: "Not Found"}[status]
    for name, value in SECURITY_HEADERS:
        assert response.headers.get_list(name.decode()) == [value.decode()]


def test_streaming_cookies_and_original_messages_are_not_buffered_or_mutated():
    original = {
        "type": "http.response.start",
        "status": 200,
        "headers": [
            (b"Set-Cookie", b"uno=sintetico"),
            (b"set-cookie", b"dos=sintetico"),
            (b"X-Frame-Options", b"DENY"),
            (b"x-frame-options", b"ALLOWALL"),
        ],
    }
    chunks = [
        {"type": "http.response.body", "body": b"a", "more_body": True},
        {"type": "http.response.body", "body": b"b", "more_body": False},
    ]
    sent = []

    async def app(scope, receive, send):
        await send(original)
        await send(chunks[0])
        assert sent[-1] is chunks[0]  # Entrega antes de producir el segundo fragmento.
        await send(chunks[1])

    async def receive():
        pytest.fail("El middleware no debe consumir el cuerpo de petición")

    async def send(message):
        sent.append(message)

    asyncio.run(DashboardHeaders(app)({"type": "http"}, receive, send))
    assert sent[0] is not original and len(original["headers"]) == 4
    assert sent[0]["headers"][:2] == original["headers"][:2]
    assert sent[1:] == chunks


@pytest.mark.parametrize("kind", ["websocket", "lifespan"])
def test_non_http_transports_receive_original_scope_and_callbacks(kind):
    scope = {"type": kind}
    called = []

    async def receive():
        return {"type": "websocket.disconnect" if kind == "websocket" else "lifespan.shutdown"}

    async def send(message):
        called.append(message)

    async def app(given_scope, given_receive, given_send):
        assert given_scope is scope and given_receive is receive and given_send is send
        await given_send(await given_receive())

    asyncio.run(DashboardHeaders(app)(scope, receive, send))
    assert len(called) == 1


def test_launcher_uses_public_streamlit_app_and_expected_script(monkeypatch):
    observed = {}
    sentinel = object()

    def create(script, middleware):
        observed.update(script=script, middleware=middleware)
        return sentinel

    monkeypatch.setattr(st, "App", create)
    namespace = runpy.run_path(str(ROOT / "dashboard" / "serve.py"))
    assert namespace["app"] is sentinel
    assert observed["script"] == ROOT / "dashboard" / "app.py"
    assert observed["middleware"][0].cls is DashboardHeaders


def test_release_tag_cannot_trigger_alternative_hf_deployment():
    workflow = yaml.load(
        (ROOT / ".github/workflows/deploy-space.yml").read_text("utf-8"), Loader=yaml.BaseLoader
    )
    assert set(workflow["on"]) == {"workflow_dispatch"}
