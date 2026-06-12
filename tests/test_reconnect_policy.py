"""Reconnect policy: indefinite retry with capped backoff, never give up.

Drives each logger's connection_loop through 100 consecutive DNS
failures — more than 3x the old 30-failure give-up limit — with the
backoff sleep faked, and asserts the loop is still retrying (it stops
only because the test sets the shutdown event, the SIGINT/SIGTERM
equivalent).
"""

import asyncio
import socket
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import venue_logger
import venue_trades_logger

N_FAILURES = 100


class _DummyWriter:
    def write(self, record: dict) -> None:  # pragma: no cover - never reached
        raise AssertionError("writer must not be touched while disconnected")


@pytest.mark.parametrize(
    ("mod", "make_args"),
    [
        (venue_logger, lambda m: (m.State("kraken"),)),
        (venue_trades_logger, lambda m: (m.State("kraken"), _DummyWriter())),
    ],
    ids=["book-logger", "trades-logger"],
)
def test_dns_failure_backs_off_forever_instead_of_exiting(
    monkeypatch: pytest.MonkeyPatch, mod, make_args
) -> None:
    mod.shutdown.clear()
    timeouts: list[float] = []

    def failing_connect(*args: object, **kwargs: object) -> object:
        raise socket.gaierror(8, "nodename nor servname provided, or not known")

    async def fake_wait_for(awaitable: object, timeout: float) -> None:
        # stands in for the backoff sleep; close the un-awaited shutdown.wait()
        if hasattr(awaitable, "close"):
            awaitable.close()
        timeouts.append(timeout)
        if len(timeouts) >= N_FAILURES:
            mod.shutdown.set()  # the only sanctioned way to stop
        raise TimeoutError  # backoff elapsed without shutdown

    monkeypatch.setattr(mod.websockets, "connect", failing_connect)
    monkeypatch.setattr(mod.asyncio, "wait_for", fake_wait_for)

    args = make_args(mod)
    rc = asyncio.run(mod.connection_loop(*args))
    mod.shutdown.clear()

    # survived far beyond the old 30-failure give-up, and stopped cleanly
    # only because shutdown was set — not via a give-up exit code
    assert len(timeouts) == N_FAILURES
    assert rc == 0
    assert args[0].reconnects == N_FAILURES
    # exponential backoff: 1,2,4,8,16,32 then capped at 60 forever
    assert timeouts[:7] == [1, 2, 4, 8, 16, 32, 60]
    assert set(timeouts[6:]) == {60}
