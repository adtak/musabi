import functools
import time
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union

from botocore.exceptions import BotoCoreError, ClientError
from openai import OpenAIError
from requests.exceptions import RequestException
from loguru import logger

from .logger import get_logger

T = TypeVar("T")


class MusabiError(Exception):
    """Base exception class for Musabi application errors."""
    
    def __init__(self, message: str, error_code: str = "MUSABI_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ValidationError(MusabiError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class ExternalServiceError(MusabiError):
    """Raised when external service calls fail."""
    
    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"{service} error: {message}", "EXTERNAL_SERVICE_ERROR", details)
        self.service = service


def handle_exceptions(
    logger_name: str,
    default_return: Any = None,
    reraise: bool = True,
) -> Callable:
    """
    Decorator for unified exception handling across Lambda functions.
    
    Args:
        logger_name: Name for the logger instance
        default_return: Default value to return on error (if reraise=False)
        reraise: Whether to reraise exceptions after logging
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, Any]]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Union[T, Any]:
            func_logger = get_logger(logger_name)
            try:
                func_logger.info(f"Starting {func.__name__}")
                result = func(*args, **kwargs)
                func_logger.info(f"Completed {func.__name__}")
                return result
            except (OpenAIError, ClientError, BotoCoreError, RequestException) as e:
                func_logger.error(f"External service error in {func.__name__}: {str(e)}")
                if reraise:
                    raise ExternalServiceError(
                        service=type(e).__name__,
                        message=str(e),
                        details={"function": func.__name__, "args": str(args), "kwargs": str(kwargs)}
                    ) from e
                return default_return
            except ValidationError as e:
                func_logger.error(f"Validation error in {func.__name__}: {e.message}")
                if reraise:
                    raise
                return default_return
            except Exception as e:
                func_logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                if reraise:
                    raise MusabiError(
                        message=f"Unexpected error in {func.__name__}",
                        error_code="UNEXPECTED_ERROR",
                        details={"original_error": str(e), "function": func.__name__}
                    ) from e
                return default_return
        return wrapper
    return decorator


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (OpenAIError, ClientError, BotoCoreError, RequestException),
) -> Callable:
    """
    Decorator for retrying functions on specific exceptions.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Factor to multiply delay by after each retry
        exceptions: Tuple of exception types to retry on
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. Retrying in {current_delay}s...")
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
                        raise
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def safe_list_access(lst: list, index: int, default: Any = None) -> Any:
    """
    Safely access list elements with a default value.
    
    Args:
        lst: List to access
        index: Index to access
        default: Default value if index is out of bounds
    
    Returns:
        Element at index or default value
    """
    try:
        return lst[index]
    except (IndexError, TypeError):
        return default


def safe_dict_access(dct: dict, key: str, default: Any = None) -> Any:
    """
    Safely access dictionary values with a default value.
    
    Args:
        dct: Dictionary to access
        key: Key to access
        default: Default value if key doesn't exist
    
    Returns:
        Value at key or default value
    """
    try:
        return dct.get(key, default)
    except (AttributeError, TypeError):
        return default


def validate_required_fields(data: dict, required_fields: list) -> None:
    """
    Validate that all required fields are present in data.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
    
    Raises:
        ValidationError: If any required field is missing
    """
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            details={"missing_fields": missing_fields, "provided_fields": list(data.keys())}
        )