import json
from collections.abc import Callable
from functools import wraps

from loguru import logger


def log_exec[T, **P](func: Callable[P, T]) -> Callable[P, T]:
    @wraps(func)
    def inner(*args: P.args, **kwargs: P.kwargs) -> T:
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

    return inner
