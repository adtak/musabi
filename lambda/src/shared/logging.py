import json
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from loguru import logger

F = TypeVar("F", bound=Callable[..., Any])


def log_exec(func: F) -> F:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        logger.info(f"{func.__name__} function called")
        logger.info(
            f"Args: {json.dumps(args, ensure_ascii=False, default=str)}",
        )
        logger.info(
            f"Kwargs: {json.dumps(kwargs, ensure_ascii=False, default=str)}",
        )
        try:
            result = func(*args, **kwargs)
            logger.info(
                f"{func.__name__} function result: "
                f"{json.dumps(result, ensure_ascii=False, default=str)}",
            )
        except Exception as e:
            logger.error(f"{func.__name__} function failed: {e!s}")
            raise
        else:
            return result

    return wrapper
