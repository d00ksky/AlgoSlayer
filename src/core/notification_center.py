"""
Asynchronous Notification Center
Queues outbound notifications and dispatches them with retries so callers
don't need to talk to Telegram directly.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional

from loguru import logger

from src.core.telegram_bot import telegram_bot


DispatchCallable = Callable[[], Awaitable[Any]]


@dataclass
class QueueItem:
    """Represents a queued notification task."""

    description: str
    coro_factory: DispatchCallable
    future: asyncio.Future
    attempt: int = 1


class NotificationCenter:
    """Simple async dispatcher with retry/backoff logic."""

    def __init__(self, max_attempts: int = 3) -> None:
        self._queue: asyncio.Queue[QueueItem] = asyncio.Queue()
        self._max_attempts = max_attempts
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False

    async def ensure_started(self) -> None:
        """Start the worker if it's not already running."""
        if self._worker_task and not self._worker_task.done():
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._worker(), name="notification-center-worker")

    async def stop(self) -> None:
        """Stop the worker and close outstanding futures."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None

        # Flush any queued items so awaiters don't hang forever
        while not self._queue.empty():
            item = self._queue.get_nowait()
            if not item.future.done():
                item.future.set_result(False)
            self._queue.task_done()

    async def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Enqueue a generic Telegram message."""
        description = f"telegram_message[{len(message)}]"
        return await self._submit(
            description=description,
            coro_factory=lambda: telegram_bot.send_message(message, parse_mode=parse_mode),
        )

    async def send_market_open_status(self, summary: Optional[dict], note: Optional[str] = None) -> bool:
        """Enqueue a market open status notification."""
        return await self._submit(
            description="market_open_status",
            coro_factory=lambda: telegram_bot.send_market_open_status(summary, note=note),
        )

    async def send_market_close_summary(
        self, summary: dict, open_positions: list[dict], note: Optional[str] = None
    ) -> bool:
        """Enqueue the market close summary."""
        return await self._submit(
            description="market_close_summary",
            coro_factory=lambda: telegram_bot.send_market_close_summary(summary, open_positions, note=note),
        )

    async def send_automated_ml_notification(self) -> bool:
        """Enqueue automated ML notification dispatch."""
        return await self._submit(
            description="automated_ml_notification",
            coro_factory=lambda: telegram_bot.send_automated_ml_notification(),
        )

    async def send_system_startup(self, trading_mode: str) -> bool:
        return await self._submit(
            description="system_startup",
            coro_factory=lambda: telegram_bot.send_system_startup(trading_mode),
        )

    async def _submit(self, description: str, coro_factory: DispatchCallable) -> bool:
        """Submit a coroutine factory to the worker and await its result."""
        await self.ensure_started()
        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()
        item = QueueItem(description=description, coro_factory=coro_factory, future=future, attempt=1)
        await self._queue.put(item)
        try:
            result = await future
            return bool(result)
        except Exception as exc:
            logger.error(f"Notification '{description}' failed: {exc}")
            return False

    async def _worker(self) -> None:
        """Worker that processes queued notifications with retries."""
        logger.info("📡 Notification center worker started")
        try:
            while self._running:
                item = await self._queue.get()
                try:
                    result = await item.coro_factory()
                    if not item.future.done():
                        item.future.set_result(result)
                except Exception as exc:
                    logger.error(f"❌ Notification dispatch error ({item.description} attempt {item.attempt}): {exc}")
                    if item.attempt < self._max_attempts:
                        self._schedule_retry(item)
                    else:
                        logger.error(f"❌ Notification giving up after {item.attempt} attempts: {item.description}")
                        if not item.future.done():
                            item.future.set_result(False)
                finally:
                    self._queue.task_done()
        except asyncio.CancelledError:
            logger.debug("🔕 Notification center worker cancelled")
        finally:
            logger.info("📡 Notification center worker stopped")

    def _schedule_retry(self, item: QueueItem) -> None:
        """Requeue the item after a backoff delay."""
        asyncio.create_task(self._retry_later(item), name=f"notification-center-retry-{item.description}")

    async def _retry_later(self, item: QueueItem) -> None:
        delay = min(30.0, 2 ** (item.attempt - 1))
        await asyncio.sleep(delay)
        if not self._running:
            if not item.future.done():
                item.future.set_result(False)
            return
        item.attempt += 1
        await self._queue.put(item)


# Global instance used across the codebase.
notification_center = NotificationCenter()
