"""Controles acotados de la demo (spec 007), sin dependencias adicionales."""

from __future__ import annotations

import sqlite3
import threading
import time
from collections import deque
from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

INFERENCE_PATHS = {"/predict", "/predict/batch", "/explain"}
RESPONSE_HEADERS = {
    b"cache-control": b"no-store",
    b"x-content-type-options": b"nosniff",
    b"referrer-policy": b"no-referrer",
}


@dataclass(frozen=True)
class Limits:
    """Perfil aprobado: un worker, presupuesto global para todos sus visitantes."""

    max_body_bytes: int = 512 * 1024
    requests_per_minute: int = 60
    max_concurrent: int = 2


DEFAULT_LIMITS = Limits()


class RequestGuards:
    """ASGI puro: límites antes de parsear JSON o efectuar inferencia."""

    def __init__(
        self, app: ASGIApp, limits: Limits = DEFAULT_LIMITS, clock: Callable = time.monotonic
    ):
        self.app, self.limits, self.clock = app, limits, clock
        self._attempts: deque[float] = deque()
        self._lock = threading.Lock()
        self._slots = threading.BoundedSemaphore(limits.max_concurrent)

    def _allow_attempt(self) -> bool:
        with self._lock:
            now = self.clock()
            while self._attempts and now - self._attempts[0] >= 60:
                self._attempts.popleft()
            if len(self._attempts) >= self.limits.requests_per_minute:
                return False
            self._attempts.append(now)
            return True

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def safe_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = [
                    (key, value)
                    for key, value in message.get("headers", [])
                    if key.lower() not in RESPONSE_HEADERS
                ]
                message = {**message, "headers": headers + list(RESPONSE_HEADERS.items())}
            await send(message)

        async def reject(status: int, detail: str, retry: str | None = None) -> None:
            headers = {"Retry-After": retry} if retry else None
            await JSONResponse({"detail": detail}, status, headers=headers)(
                scope, receive, safe_send
            )

        lengths = [v for k, v in scope.get("headers", []) if k.lower() == b"content-length"]
        if lengths:
            try:
                declared = [int(v) for v in lengths]
            except ValueError:
                await reject(400, "Content-Length no válido.")
                return
            if any(v < 0 for v in declared) or len(set(declared)) != 1:
                await reject(400, "Content-Length no válido.")
                return
            if declared[0] > self.limits.max_body_bytes:
                await reject(413, "La petición supera el tamaño permitido.")
                return

        protected = scope["method"] == "POST" and scope["path"] in INFERENCE_PATHS
        acquired = False
        if protected:
            if not self._allow_attempt():
                await reject(429, "Límite de peticiones por minuto alcanzado.", "60")
                return
            acquired = self._slots.acquire(blocking=False)
            if not acquired:
                await reject(429, "Servicio ocupado; vuelve a intentarlo.", "1")
                return
        try:
            # El límite también funciona con cuerpos fragmentados o sin Content-Length.
            body = bytearray()
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                chunk = message.get("body", b"")
                if len(body) + len(chunk) > self.limits.max_body_bytes:
                    await reject(413, "La petición supera el tamaño permitido.")
                    return
                body.extend(chunk)
                if not message.get("more_body", False):
                    break
            delivered = False

            async def replay() -> Message:
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await receive()

            await self.app(scope, replay, safe_send)
        finally:
            if acquired:
                self._slots.release()


class SQLiteHourlyLimiter:
    """Cuota LLM persistida y atómica para procesos que comparten el mismo archivo."""

    def __init__(self, path: Path, clock: Callable = time.time, window: float = 3600):
        self.path, self.clock, self.window = Path(path), clock, window

    def try_acquire(self, limit: int) -> bool:
        if limit <= 0:
            return False
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=1.0)) as connection:
            self.path.chmod(0o600)
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("CREATE TABLE IF NOT EXISTS attempts (timestamp REAL NOT NULL)")
                now = self.clock()
                connection.execute(
                    "DELETE FROM attempts WHERE timestamp <= ?", (now - self.window,)
                )
                count = connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
                if count >= limit:
                    return False
                connection.execute("INSERT INTO attempts (timestamp) VALUES (?)", (now,))
                return True
