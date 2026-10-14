"""Respuestas sintéticas: no red ni datos/cookies de un servicio público."""

import json
import ssl
from email.message import Message

import pytest
from scripts import verify_public_security as public

HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=31536000",
    "X-Frame-Options": "SAMEORIGIN",
}


@pytest.mark.parametrize(
    "url",
    [
        "http://demo.onrender.com",
        "https://user:password@demo.onrender.com",
        "https://localhost",
        "https://127.0.0.1",
        "https://demo.onrender.com?token=x",
    ],
)
def test_invalid_target_is_rejected_without_network(url):
    with pytest.raises(ValueError):
        public.normalize_url(url)


def test_cookie_values_are_never_reported_and_xsrf_is_not_required_to_be_httponly():
    result = public.inspect_cookies(("_streamlit_xsrf=valor-privado; SameSite=None; Secure",))
    assert result["status"] == "passed" and not result["cookies"][0]["http_only"]
    assert "valor-privado" not in json.dumps(result)
    assert (
        public.inspect_cookies(("_streamlit_xsrf=valor-privado; SameSite=None",))["status"]
        == "failed"
    )
    assert public.inspect_cookies(())["status"] == "not_verified"


def test_header_absence_or_disabled_hsts_is_not_green():
    assert any(c["status"] == "failed" for c in public.inspect_headers({}))
    headers = {**HEADERS, "Strict-Transport-Security": "max-age=0"}
    assert (
        next(c for c in public.inspect_headers(headers) if c["check"] == "hsts")["status"]
        == "failed"
    )


def test_checks_use_only_synthetic_responses_and_require_comparison_of_origins():
    calls = []

    def request(url, headers=None):
        calls.append((url, headers))
        if url.startswith("http://"):
            return public.Response(301, {"Location": "https://demo.onrender.com/"})
        if url.endswith("_stcore/stream"):
            status = 101 if headers["Origin"] == "https://demo.onrender.com" else 403
            return public.Response(status, {})
        cookies = (
            ("_streamlit_xsrf=privado; SameSite=Lax; Secure",)
            if url.endswith("_stcore/health")
            else ()
        )
        return public.Response(200, HEADERS, cookies)

    report, code = public.verify("https://demo.onrender.com", request)
    assert code == 0 and report["status"] == "passed"
    assert "privado" not in json.dumps(report)
    assert len(calls) == 6

    def blocked(url, headers=None):
        return public.Response(403, {})

    report, code = public.verify("https://demo.onrender.com", blocked)
    assert code != 0
    origin = next(c for c in report["checks"] if c["check"] == "websocket_origin")
    assert origin["status"] == "not_verified"  # Un 403 general no demuestra CORS.


def test_failed_health_never_becomes_green_even_with_valid_cookie():
    def request(url, headers=None):
        if url.startswith("http://"):
            return public.Response(301, {"Location": "https://demo.onrender.com/"})
        if url.endswith("_stcore/stream"):
            return public.Response(
                101 if headers["Origin"] == "https://demo.onrender.com" else 403, {}
            )
        if url.endswith("_stcore/health"):
            return public.Response(503, {}, ("_streamlit_xsrf=sintetico; SameSite=Lax",))
        return public.Response(200, HEADERS)

    report, code = public.verify("https://demo.onrender.com", request)
    assert code == 2 and report["status"] == "not_verified"
    assert (
        next(row for row in report["checks"] if row["check"] == "dashboard_health")["status"]
        == "not_verified"
    )


def test_cli_without_url_never_fetches(monkeypatch, capsys):
    monkeypatch.setattr(public, "verify", lambda _: pytest.fail("No debe usar red"))
    assert public.main([]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "not_verified"


def test_permissive_csp_is_not_hidden_by_restrictive_x_frame_options():
    headers = {**HEADERS, "Content-Security-Policy": "frame-ancestors *"}
    framing = next(c for c in public.inspect_headers(headers) if c["check"] == "framing")
    assert framing["status"] == "failed"


def test_https_transport_preserves_upgrade_verifies_tls_and_never_reads_body(monkeypatch):
    observed = {}
    headers = Message()
    headers.add_header("Set-Cookie", "_xsrf=solo-sintetico; SameSite=Lax")

    class FakeResponse:
        status = 101

        def read(self):
            pytest.fail("No debe leer cuerpos")

        def close(self):
            observed["response_closed"] = True

    class FakeConnection:
        def __init__(self, host, timeout, context):
            assert host == "demo.onrender.com"
            assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED

        def request(self, method, path, headers):
            assert method == "GET" and path == "/_stcore/stream"
            assert headers["Connection"] == "Upgrade"

        def getresponse(self):
            response = FakeResponse()
            response.headers = headers
            return response

        def close(self):
            observed["connection_closed"] = True

    monkeypatch.setattr(public.http.client, "HTTPSConnection", FakeConnection)
    response = public.fetch("https://demo.onrender.com/_stcore/stream", {"Connection": "Upgrade"})
    assert response.status == 101
    assert observed == {"response_closed": True, "connection_closed": True}
