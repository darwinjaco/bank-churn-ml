"""Cabeceras del dashboard público sin alterar transporte/estado (spec 007 v1.2)."""

from __future__ import annotations

from starlette.types import ASGIApp, Message, Receive, Scope, Send

SECURITY_HEADERS = (
    (b"x-content-type-options", b"nosniff"),
    (b"referrer-policy", b"no-referrer"),
    (b"strict-transport-security", b"max-age=31536000"),
    (b"x-frame-options", b"SAMEORIGIN"),
    (b"content-security-policy", b"frame-ancestors 'self'"),
)


class DashboardHeaders:
    """Middleware ASGI sin buffer; WebSocket y lifespan se delegan intactos."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                protected = {key for key, _ in SECURITY_HEADERS}
                headers = [
                    (key, value)
                    for key, value in message.get("headers", [])
                    if key.lower() not in protected
                ]
                message = {**message, "headers": headers + list(SECURITY_HEADERS)}
            await send(message)

        await self.app(scope, receive, with_headers)
