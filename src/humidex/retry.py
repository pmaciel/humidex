"""Shared retry logic with exponential backoff."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    base_backoff: float = 1.0,
    rate_limit_multiplier: float = 2.0,
    is_rate_limited: Callable[[Exception], bool] | None = None,
    no_retry: tuple[type[Exception], ...] = (),
) -> T:
    """Execute a function with exponential backoff retry.

    Args:
        func: Function to execute.
        max_retries: Maximum number of retries.
        base_backoff: Base backoff in seconds.
        rate_limit_multiplier: Multiplier applied to delay when rate-limited.
        is_rate_limited: Optional predicate to detect rate-limit exceptions.
        no_retry: Exception types that should never be retried.

    Returns:
        Result of the function.

    Raises:
        The last exception if all retries fail, or any exception in no_retry.
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            if isinstance(e, no_retry):
                raise
            last_exception = e
            if attempt < max_retries:
                if is_rate_limited and is_rate_limited(e):
                    multiplier = rate_limit_multiplier
                else:
                    multiplier = 1.0
                delay = base_backoff * (2**attempt) * multiplier
                logger.warning(
                    "Attempt %d/%d failed, retrying in %.1fs: %s",
                    attempt + 1,
                    max_retries + 1,
                    delay,
                    e,
                )
                time.sleep(delay)
            continue

    assert last_exception is not None  # loop always sets this before exit
    raise last_exception
