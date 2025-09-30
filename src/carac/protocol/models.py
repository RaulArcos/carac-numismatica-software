from enum import Enum
from typing import Any, Dict
import json

from pydantic import BaseModel, Field


class CommandType(str, Enum):
    LIGHTING = "lighting"
    PHOTO_SEQUENCE = "photo_sequence"
    PING = "ping"
    STATUS = "status"
    LED_TOGGLE = "led_toggle"


class ConnectionStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class Command(BaseModel):
    type: CommandType
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float | None = None
    
    def to_serial(self) -> str:
        payload = {
            "type": self.type.value,
            "data": self.data,
        }
        if self.timestamp is not None:
            payload["timestamp"] = self.timestamp
        return json.dumps(payload) + "\n"


class Response(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float | None = None
    
    @classmethod
    def from_serial(cls, data: str) -> "Response":
        try:
            if not data or not data.strip():
                return cls(
                    success=False,
                    message="Empty response received",
                    data={"raw": data}
                )
            
            parsed = json.loads(data.strip())
            return cls(**parsed)
        except (json.JSONDecodeError, ValueError) as e:
            return cls(
                success=False,
                message=f"Failed to parse response: {e}",
                data={"raw": data}
            )


class LightingCommand(Command):
    type: CommandType = Field(default=CommandType.LIGHTING, init=False)
    
    def __init__(self, channel: str, intensity: int, **kwargs: Any) -> None:
        super().__init__(
            type=CommandType.LIGHTING,
            data={"channel": channel, "intensity": intensity},
            **kwargs
        )


class PhotoSequenceCommand(Command):
    type: CommandType = Field(default=CommandType.PHOTO_SEQUENCE, init=False)
    
    def __init__(self, count: int = 5, delay: float = 1.0, **kwargs: Any) -> None:
        super().__init__(
            type=CommandType.PHOTO_SEQUENCE,
            data={"count": count, "delay": delay},
            **kwargs
        )


class PingCommand(Command):
    type: CommandType = Field(default=CommandType.PING, init=False)
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            type=CommandType.PING,
            data={"ping": True},
            **kwargs
        )


class StatusCommand(Command):
    type: CommandType = Field(default=CommandType.STATUS, init=False)
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            type=CommandType.STATUS,
            data={"status": True},
            **kwargs
        )


class LedToggleCommand(Command):
    type: CommandType = Field(default=CommandType.LED_TOGGLE, init=False)
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            type=CommandType.LED_TOGGLE,
            data={"toggle": True},
            **kwargs
        )