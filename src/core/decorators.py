"""
Aletheia Utility Decorators

Collection of reusable decorators for common cross-cutting concerns:

    - Performance measurement
    - Caching with expiration
    - Retry with exponential backoff
    - Rate limiting
    - Validation
    - Error handling

These decorators follow best practices:
    - Preserve function signatures (functools.wraps)
    - Type hints for parameters and returns
    - Configurable behavior
    - Logging integration
"""

from __future__ import annotations

import asyncio
import functools
import hashlib
import logging
import time
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

from django.core.cache import cache

from .exceptions import AletheiaError, ProcessingError

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def timer(
    log_level: int = logging.DEBUG,
    message_template: str = "{func_name} executed in {duration:.4f}s",
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to measure and log function execution time.
    
    Args:
        log_level: Logging level for the timing message.
        message_template: Template for the log message.
            Available placeholders: {func_name}, {duration}
    
    Returns:
        Decorated function that logs execution time.
    
    Example:
        >>> @timer(log_level=logging.INFO)
        ... def slow_function():
        ...     time.sleep(1)
        ...
        >>> slow_function()  # Logs: "slow_function executed in 1.0001s"
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start_time
                logger.log(
                    log_level,
                    message_template.format(func_name=func.__name__, duration=duration),
                    extra={
                        "function": func.__name__,
                        "duration_seconds": duration,
                    },
                )
        return wrapper
    return decorator


def async_timer(
    log_level: int = logging.DEBUG,
    message_template: str = "{func_name} executed in {duration:.4f}s",
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Async version of timer decorator.
    
    Args:
        log_level: Logging level for the timing message.
        message_template: Template for the log message.
    
    Returns:
        Decorated async function that logs execution time.
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start_time
                logger.log(
                    log_level,
                    message_template.format(func_name=func.__name__, duration=duration),
                )
        return wrapper
    return decorator


def cached(
    ttl: int = 300,
    key_prefix: str = "func_cache",
    key_builder: Callable[..., str] | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to cache function results with expiration.
    
    Uses Django's cache backend. Results are cached based on function
    arguments unless a custom key_builder is provided.
    
    Args:
        ttl: Time-to-live in seconds (default: 5 minutes).
        key_prefix: Prefix for cache keys.
        key_builder: Optional function to generate cache key from args.
    
    Returns:
        Decorated function with caching behavior.
    
    Example:
        >>> @cached(ttl=60, key_prefix="model_predictions")
        ... def predict(model_name: str, video_id: str) -> dict:
        ...     # Expensive computation
        ...     return {"result": "fake"}
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key builder using hash of arguments
                key_parts = [
                    key_prefix,
                    func.__module__,
                    func.__name__,
                    hashlib.md5(
                        f"{args}:{sorted(kwargs.items())}".encode()
                    ).hexdigest()[:12],
                ]
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {cache_key}, cached for {ttl}s")
            
            return result
        
        # Add cache invalidation method
        def invalidate(*args: Any, **kwargs: Any) -> None:
            """Invalidate cached value for given arguments."""
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                key_parts = [
                    key_prefix,
                    func.__module__,
                    func.__name__,
                    hashlib.md5(
                        f"{args}:{sorted(kwargs.items())}".encode()
                    ).hexdigest()[:12],
                ]
                cache_key = ":".join(key_parts)
            cache.delete(cache_key)
            logger.debug(f"Cache invalidated for {cache_key}")
        
        wrapper.invalidate = invalidate  # type: ignore
        return wrapper
    return decorator


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    on_retry: Callable[[Exception, int], None] | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for automatic retry with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts (including initial).
        delay: Initial delay between retries in seconds.
        backoff_factor: Multiplier for delay after each retry.
        exceptions: Tuple of exception types to catch and retry.
        on_retry: Optional callback called on each retry with (exception, attempt).
    
    Returns:
        Decorated function with retry behavior.
    
    Example:
        >>> @retry(max_attempts=3, delay=1.0, exceptions=(ConnectionError,))
        ... def fetch_data(url: str) -> dict:
        ...     response = requests.get(url)
        ...     return response.json()
    
    Raises:
        The last exception if all retries are exhausted.
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            current_delay = delay
            last_exception: Exception | None = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts",
                            extra={
                                "function": func.__name__,
                                "attempts": max_attempts,
                                "error": str(e),
                            },
                        )
                        raise
                    
                    logger.warning(
                        f"{func.__name__} attempt {attempt} failed: {e}. "
                        f"Retrying in {current_delay:.1f}s...",
                    )
                    
                    if on_retry:
                        on_retry(e, attempt)
                    
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
            
            # This should never be reached, but just in case
            raise last_exception  # type: ignore
        
        return wrapper
    return decorator


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Async version of retry decorator.
    
    Args:
        max_attempts: Maximum number of attempts.
        delay: Initial delay between retries in seconds.
        backoff_factor: Multiplier for delay after each retry.
        exceptions: Tuple of exception types to catch and retry.
    
    Returns:
        Decorated async function with retry behavior.
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        raise
                    
                    logger.warning(
                        f"{func.__name__} attempt {attempt} failed: {e}. "
                        f"Retrying in {current_delay:.1f}s...",
                    )
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_factor
            
            raise RuntimeError("Retry logic failed unexpectedly")
        
        return wrapper
    return decorator


def validate_input(
    *validators: Callable[..., None],
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to validate function inputs before execution.
    
    Validators are functions that take the same arguments as the decorated
    function and raise an exception if validation fails.
    
    Args:
        *validators: Validator functions to run before the decorated function.
    
    Returns:
        Decorated function that validates inputs first.
    
    Example:
        >>> def validate_positive(x: int) -> None:
        ...     if x <= 0:
        ...         raise ValueError("x must be positive")
        ...
        >>> @validate_input(validate_positive)
        ... def process(x: int) -> int:
        ...     return x * 2
        ...
        >>> process(-1)  # Raises ValueError
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            for validator in validators:
                validator(*args, **kwargs)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def handle_errors(
    error_mapping: dict[type[Exception], type[AletheiaError]] | None = None,
    default_error_class: type[AletheiaError] = ProcessingError,
    log_errors: bool = True,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to convert exceptions to Aletheia error types.
    
    Maps specific exception types to corresponding AletheiaError subclasses
    for consistent error handling across the application.
    
    Args:
        error_mapping: Dict mapping exception types to AletheiaError types.
        default_error_class: Default error class for unmapped exceptions.
        log_errors: Whether to log caught exceptions.
    
    Returns:
        Decorated function with error transformation.
    
    Example:
        >>> @handle_errors(error_mapping={FileNotFoundError: ModelNotFoundError})
        ... def load_model(path: str) -> Model:
        ...     return torch.load(path)
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except AletheiaError:
                # Already an Aletheia error, re-raise
                raise
            except Exception as e:
                if log_errors:
                    logger.exception(f"Error in {func.__name__}: {e}")
                
                # Check for mapped error types
                if error_mapping:
                    for exc_type, error_class in error_mapping.items():
                        if isinstance(e, exc_type):
                            raise error_class(message=str(e)) from e
                
                # Use default error class
                raise default_error_class(message=str(e)) from e
        
        return wrapper
    return decorator


def deprecated(
    message: str = "",
    version: str = "",
    replacement: str = "",
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Mark a function as deprecated.
    
    Logs a deprecation warning when the function is called.
    
    Args:
        message: Additional deprecation message.
        version: Version when the function was deprecated.
        replacement: Suggested replacement function/method.
    
    Returns:
        Decorated function that logs deprecation warning.
    
    Example:
        >>> @deprecated(version="2.0.0", replacement="new_function")
        ... def old_function():
        ...     pass
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            warning_parts = [f"{func.__name__} is deprecated"]
            
            if version:
                warning_parts.append(f"(since version {version})")
            if replacement:
                warning_parts.append(f"Use {replacement} instead")
            if message:
                warning_parts.append(f"Note: {message}")
            
            logger.warning(" - ".join(warning_parts))
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def singleton(cls: type[T]) -> type[T]:
    """
    Decorator to make a class a singleton.
    
    Ensures only one instance of the class exists.
    
    Args:
        cls: Class to make singleton.
    
    Returns:
        Decorated class that returns same instance on each call.
    
    Example:
        >>> @singleton
        ... class Config:
        ...     def __init__(self):
        ...         self.value = 42
        ...
        >>> c1 = Config()
        >>> c2 = Config()
        >>> c1 is c2  # True
    """
    instances: dict[type, Any] = {}
    
    @functools.wraps(cls, updated=[])
    def get_instance(*args: Any, **kwargs: Any) -> T:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance  # type: ignore
