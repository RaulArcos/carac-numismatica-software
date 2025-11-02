from typing import Callable, Generic, TypeVar

from loguru import logger

T = TypeVar("T")


class CallbackManager(Generic[T]):
    def __init__(self) -> None:
        self._callbacks: list[Callable[[T], None]] = []
    
    def add(self, callback: Callable[[T], None]) -> None:
        if callback not in self._callbacks:
            self._callbacks.append(callback)
    
    def notify(self, value: T) -> None:
        for callback in self._callbacks:
            try:
                callback(value)
            except Exception as e:
                logger.error(f"Error in callback: {e}")
