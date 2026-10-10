"""Casos adversarios sintéticos: sin red, modelo real, credenciales ni datos de clientes."""

import asyncio
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

import pytest
from starlette.responses import JSONResponse

from churn.security import Limits, RequestGuards, SQLiteHourlyLimiter


async def _echo(scope, receive, send):
    message = await receive()
    await JSONResponse({"bytes": len(message.get("body", b""))})(scope, receive, send)


async def _call(app, chunks=(b"{}",), headers=(), path="/predict", method="POST"):
    messages = [
        {"type": "http.request", "body": chunk, "more_body": i < len(chunks) - 1}
        for i, chunk in enumerate(chunks)
    ]
    output = []

    async def receive():
        return messages.pop(0) if messages else {"type": "http.disconnect"}

    async def send(message):
        output.append(message)

    await app({"type": "http", "method": method, "path": path, "headers": headers}, receive, send)
    return output


def _status(output):
    return next(message["status"] for message in output if message["type"] == "http.response.start")


@pytest.mark.parametrize("headers", [(), ((b"content-length", b"2"),)])
def test_body_limit_counts_chunks_even_if_header_is_missing_or_false(headers):
    guard = RequestGuards(_echo, Limits(max_body_bytes=4))
    assert _status(asyncio.run(_call(guard, (b"123", b"45"), headers))) == 413
    assert _status(asyncio.run(_call(guard, (b"1234",)))) == 200


@pytest.mark.parametrize("value, status", [(b"5", 413), (b"bad", 400), (b"-1", 400)])
def test_invalid_or_oversized_content_length_is_rejected(value, status):
    guard = RequestGuards(_echo, Limits(max_body_bytes=4))
    assert _status(asyncio.run(_call(guard, headers=((b"content-length", value),)))) == status


def test_rate_window_and_health_availability():
    now = [0.0]
    guard = RequestGuards(_echo, Limits(requests_per_minute=1), clock=lambda: now[0])
    assert _status(asyncio.run(_call(guard))) == 200
    limited = asyncio.run(_call(guard))
    assert _status(limited) == 429
    headers = dict(limited[0]["headers"])
    assert headers[b"retry-after"] == b"60" and headers[b"cache-control"] == b"no-store"
    assert _status(asyncio.run(_call(guard, path="/health", method="GET"))) == 200
    now[0] = 60
    assert _status(asyncio.run(_call(guard))) == 200


def test_concurrency_rejection_and_slot_release():
    async def scenario():
        entered = asyncio.Event()
        release = asyncio.Event()
        active = [0]

        async def slow(scope, receive, send):
            active[0] += 1
            if active[0] == 2:
                entered.set()
            await release.wait()
            await _echo(scope, receive, send)

        guard = RequestGuards(slow)
        first = asyncio.create_task(_call(guard))
        second = asyncio.create_task(_call(guard))
        await asyncio.wait_for(entered.wait(), 5)
        assert _status(await _call(guard)) == 429
        release.set()
        assert [_status(result) for result in await asyncio.gather(first, second)] == [200, 200]
        assert _status(await _call(guard)) == 200

    asyncio.run(scenario())


def test_slot_is_released_when_application_fails():
    calls = [0]

    async def flaky(scope, receive, send):
        calls[0] += 1
        if calls[0] == 1:
            raise RuntimeError("fallo sintético")
        await _echo(scope, receive, send)

    guard = RequestGuards(flaky, Limits(max_concurrent=1))
    with pytest.raises(RuntimeError):
        asyncio.run(_call(guard))
    assert _status(asyncio.run(_call(guard))) == 200


def test_quota_is_atomic_shared_and_persistent(tmp_path):
    path = tmp_path / "state" / "quota.sqlite3"
    now = [1000.0]

    def reserve(_):
        return SQLiteHourlyLimiter(path, clock=lambda: now[0]).try_acquire(3)

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(reserve, range(12))) == 3
    assert not SQLiteHourlyLimiter(path, clock=lambda: now[0]).try_acquire(3)
    now[0] += 3600
    assert SQLiteHourlyLimiter(path, clock=lambda: now[0]).try_acquire(3)


def test_zero_quota_creates_no_database(tmp_path):
    path = tmp_path / "absent" / "quota.sqlite3"
    assert not SQLiteHourlyLimiter(path).try_acquire(0)
    assert not path.parent.exists()


def _reserve_in_process(path):
    return SQLiteHourlyLimiter(Path(path)).try_acquire(3)


def test_quota_is_shared_between_separate_processes(tmp_path):
    path = tmp_path / "processes.sqlite3"
    with ProcessPoolExecutor(
        max_workers=2, mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        assert sum(pool.map(_reserve_in_process, [str(path)] * 8)) == 3
    assert not SQLiteHourlyLimiter(path).try_acquire(3)
