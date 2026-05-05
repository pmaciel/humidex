"""Tests for retry module."""

from unittest.mock import MagicMock, patch

import pytest

from humidex.retry import retry_with_backoff


class TestRetryWithBackoff:
    """Tests for retry_with_backoff."""

    def test_success_first_attempt(self) -> None:
        func = MagicMock(return_value=42)
        result = retry_with_backoff(func, max_retries=3, base_backoff=0.01)

        assert result == 42
        assert func.call_count == 1

    def test_success_after_retry(self) -> None:
        func = MagicMock(side_effect=[ValueError("fail"), ValueError("fail"), "ok"])

        with patch("humidex.retry.time.sleep"):
            result = retry_with_backoff(func, max_retries=3, base_backoff=0.01)

        assert result == "ok"
        assert func.call_count == 3

    def test_raises_after_max_retries(self) -> None:
        func = MagicMock(side_effect=ValueError("fail"))

        with patch("humidex.retry.time.sleep"):
            with pytest.raises(ValueError, match=r"^fail$") as exc_info:
                retry_with_backoff(func, max_retries=2, base_backoff=0.01)

        assert exc_info.type is ValueError
        assert exc_info.value.args == ("fail",)
        assert func.call_count == 3

    def test_rate_limit_multiplier(self) -> None:
        func = MagicMock(side_effect=Exception("rate limited"))

        with patch("humidex.retry.time.sleep") as mock_sleep:
            with pytest.raises(Exception, match=r"^rate limited$"):
                retry_with_backoff(
                    func,
                    max_retries=2,
                    base_backoff=1.0,
                    rate_limit_multiplier=2.0,
                    is_rate_limited=lambda e: True,
                )

        delays = [call[0][0] for call in mock_sleep.call_args_list]
        assert delays[0] == 2.0
        assert delays[1] == 4.0

    def test_no_retry_for_non_retryable(self) -> None:
        func = MagicMock(side_effect=KeyboardInterrupt())

        with pytest.raises(KeyboardInterrupt):
            retry_with_backoff(func, max_retries=3, base_backoff=0.01)

        assert func.call_count == 1

    def test_no_retry_tuple_skips_retry(self) -> None:
        func = MagicMock(side_effect=ValueError("bad input"))

        with patch("humidex.retry.time.sleep") as mock_sleep:
            with pytest.raises(ValueError, match=r"^bad input$"):
                retry_with_backoff(
                    func,
                    max_retries=3,
                    base_backoff=0.01,
                    no_retry=(ValueError,),
                )

        assert func.call_count == 1
        mock_sleep.assert_not_called()

    def test_rate_limit_path_with_no_retry_set(self) -> None:
        """Rate-limited exc should retry when no_retry contains other types."""

        class RateLimitError(Exception):
            pass

        class FatalError(Exception):
            pass

        func = MagicMock(side_effect=[RateLimitError("slow down"), "ok"])

        with patch("humidex.retry.time.sleep") as mock_sleep:
            result = retry_with_backoff(
                func,
                max_retries=2,
                base_backoff=1.0,
                rate_limit_multiplier=2.0,
                is_rate_limited=lambda e: isinstance(e, RateLimitError),
                no_retry=(FatalError,),
            )

        assert result == "ok"
        assert func.call_count == 2
        # First retry: base_backoff * 2**0 * multiplier = 1.0 * 1 * 2.0 = 2.0
        mock_sleep.assert_called_once_with(2.0)

    def test_reraised_exception_preserves_type_and_args(self) -> None:
        class CustomError(Exception):
            pass

        original = CustomError("boom", 42, {"key": "value"})
        func = MagicMock(side_effect=original)

        with patch("humidex.retry.time.sleep"):
            with pytest.raises(CustomError) as exc_info:
                retry_with_backoff(func, max_retries=2, base_backoff=0.01)

        assert exc_info.type is CustomError
        assert exc_info.value.args == ("boom", 42, {"key": "value"})
        assert exc_info.value is original
