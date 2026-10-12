"""Comprobación manual de seguridad pública, sin credenciales ni datos de clientes (spec 007 §9)."""

from __future__ import annotations

import argparse
import base64
import http.client
import ipaddress
import json
import re
import secrets
import ssl
from dataclasses import dataclass
from http.cookies import CookieError, SimpleCookie
from urllib.parse import urlsplit


@dataclass
class Response:
    status: int
    headers: dict
    cookies: tuple[str, ...] = ()


def normalize_url(value: str) -> str:
    parts = urlsplit(value)
    host = parts.hostname or ""
    if (
        parts.scheme != "https"
        or not host
        or parts.username is not None
        or parts.password is not None
        or parts.query
        or parts.fragment
        or parts.path not in ("", "/")
        or parts.port not in (None, 443)
        or not re.fullmatch(r"[A-Za-z0-9.-]+", host)
        or host == "localhost"
        or host.endswith((".localhost", ".local", ".internal"))
    ):
        raise ValueError("Se requiere la URL HTTPS raíz de la demo pública, sin credenciales.")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("No se aceptan direcciones locales o reservadas.")
    return f"https://{host}/"


def fetch(url: str, headers: dict | None = None) -> Response:
    parts = urlsplit(url)
    # urllib fuerza Connection: close; http.client conserva el handshake Upgrade.
    connection = (
        http.client.HTTPSConnection(
            parts.hostname, timeout=30, context=ssl.create_default_context()
        )
        if parts.scheme == "https"
        else http.client.HTTPConnection(parts.hostname, timeout=30)
    )
    try:
        connection.request(
            "GET",
            parts.path or "/",
            headers={"User-Agent": "bank-churn-security-check", **(headers or {})},
        )
        response = connection.getresponse()
        try:
            return Response(
                response.status,
                dict(response.headers),
                tuple(response.headers.get_all("Set-Cookie", [])),
            )
        finally:
            response.close()
    finally:
        connection.close()  # No lee cuerpos, no sigue redirects ni guarda valores.


def check(name: str, status: str, detail: str) -> dict:
    return {"check": name, "status": status, "detail": detail}


def inspect_headers(headers: dict) -> list[dict]:
    lower = {key.lower(): value for key, value in headers.items()}
    checks = []
    for key, expected in (
        ("x-content-type-options", "nosniff"),
        ("referrer-policy", "no-referrer"),
    ):
        value = lower.get(key, "").lower()
        accepted = (
            value == expected
            if key == "x-content-type-options"
            else value
            in {"no-referrer", "same-origin", "strict-origin", "strict-origin-when-cross-origin"}
        )
        checks.append(
            check(
                key,
                "passed" if accepted else "failed",
                "Política presente" if accepted else "Política ausente o no restrictiva",
            )
        )
    hsts = lower.get("strict-transport-security", "")
    match = re.search(r"(?:^|;)\s*max-age\s*=\s*(\d+)", hsts, re.I)
    checks.append(
        check(
            "hsts",
            "passed" if match and int(match[1]) > 0 else "failed",
            "Se exige max-age positivo en HTTPS",
        )
    )
    xfo = lower.get("x-frame-options", "").upper()
    csp = lower.get("content-security-policy", "")
    frame = re.search(r"(?:^|;)\s*frame-ancestors\s+([^;]+)", csp, re.I)
    if frame:  # frame-ancestors tiene precedencia sobre X-Frame-Options.
        if frame[1].strip() in {"'self'", "'none'"}:
            framing = "passed"
        else:
            framing = "failed" if "*" in frame[1] else "not_verified"
    elif xfo in {"DENY", "SAMEORIGIN"}:
        framing = "passed"
    else:
        framing = "failed" if xfo else "not_verified"
    checks.append(check("framing", framing, "Evaluación limitada a framing, no de toda la CSP"))
    return checks


def inspect_cookies(values: tuple[str, ...]) -> dict:
    observed = []
    for value in values:
        cookie = SimpleCookie()
        try:
            cookie.load(value)
        except CookieError:
            continue
        for name, morsel in cookie.items():
            if name not in {"_streamlit_xsrf", "_xsrf"}:
                continue
            same_site = morsel["samesite"].lower()
            observed.append(
                {
                    "name": name,
                    "same_site": same_site if same_site in {"lax", "strict", "none"} else "invalid",
                    "secure": bool(morsel["secure"]),
                    "http_only": bool(morsel["httponly"]),
                }
            )
    if not observed:
        return {**check("xsrf_cookie", "not_verified", "Cookie XSRF no observada"), "cookies": []}
    valid = all(
        c["same_site"] != "invalid" and (c["same_site"] != "none" or c["secure"]) for c in observed
    )
    return {
        **check(
            "xsrf_cookie",
            "passed" if valid else "failed",
            "SameSite evaluado; HttpOnly no se exige al token que lee el frontend",
        ),
        "cookies": observed,
    }


def verify(url: str, requester=fetch) -> tuple[dict, int]:
    base = normalize_url(url)
    root = requester(base)
    plain = requester(base.replace("https://", "http://", 1))
    location = {k.lower(): v for k, v in plain.headers.items()}.get("location", "")
    destination = urlsplit(location)
    redirected = plain.status in {301, 302, 303, 307, 308} and (
        destination.scheme == "https"
        and destination.hostname == urlsplit(base).hostname
        and destination.username is None
        and destination.password is None
        and destination.port in (None, 443)
    )
    checks = [
        check(
            "tls_and_page",
            "passed" if root.status == 200 else "not_verified",
            "Certificado verificado por el cliente HTTPS; se espera página 200",
        ),
        check(
            "http_to_https",
            "passed" if redirected else "failed",
            "Redirección a HTTPS del mismo dominio",
        ),
        *inspect_headers(root.headers),
    ]
    config = requester(base + "_stcore/host-config")
    checks.append(inspect_cookies(root.cookies + config.cookies))
    key = base64.b64encode(secrets.token_bytes(16)).decode("ascii")
    websocket = {
        "Upgrade": "websocket",
        "Connection": "Upgrade",
        "Sec-WebSocket-Version": "13",
        "Sec-WebSocket-Key": key,
        "Sec-WebSocket-Protocol": "streamlit",
    }
    endpoint = base + "_stcore/stream"
    allowed = requester(endpoint, {**websocket, "Origin": base.rstrip("/")})
    denied = requester(endpoint, {**websocket, "Origin": "https://origen-no-autorizado.invalid"})
    origin_status = (
        "not_verified"
        if allowed.status != 101
        else ("passed" if denied.status == 403 else "failed")
    )
    checks.append(
        check(
            "websocket_origin",
            origin_status,
            "Se exige origen propio 101 y origen ajeno 403; no se envían mensajes",
        )
    )
    states = {entry["status"] for entry in checks}
    code = 1 if "failed" in states else (2 if "not_verified" in states else 0)
    return {
        "url": base,
        "status": "failed" if code == 1 else ("not_verified" if code == 2 else "passed"),
        "checks": checks,
        "limits": "No certifica subidas/iframe en navegador ni toda la CSP",
    }, code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="URL HTTPS pública raíz, sin tokens ni parámetros")
    args = parser.parse_args(argv)
    if not args.url:
        report, code = {"status": "not_verified", "reason": "Falta URL pública"}, 2
    else:
        try:
            report, code = verify(args.url)
        except ValueError:
            report, code = {"status": "failed", "reason": "URL pública no válida"}, 1
        except (OSError, http.client.HTTPException):
            report, code = {"status": "not_verified", "reason": "No se pudo verificar red/TLS"}, 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
