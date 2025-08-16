from enum import Enum
from typing import Any, Dict, Optional

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
    timestamp: Optional[float] = None
    
    def to_serial(self) -> str:
        import json
        return json.dumps(self.model_dump()) + "\n"


class Response(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[float] = None
    
    @classmethod
    def from_serial(cls, data: str) -> "Response":
        import json
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
    type: CommandType = Field(default=CommandType.LIGHTING, frozen=True)
    channel: str = Field(..., description="Lighting channel name")
    intensity: int = Field(..., ge=0, le=255, description="Lighting intensity (0-255)")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.data = {
            "channel": self.channel,
            "intensity": self.intensity
        }


class PhotoSequenceCommand(Command):
    type: CommandType = Field(default=CommandType.PHOTO_SEQUENCE, frozen=True)
    count: int = Field(default=5, ge=1, le=100, description="Number of photos to take")
    delay: float = Field(default=1.0, ge=0.1, le=10.0, description="Delay between photos")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.data = {
            "count": self.count,
            "delay": self.delay
        }


class PingCommand(Command):
    type: CommandType = Field(default=CommandType.PING, frozen=True)
    
    def __init__(self, **data):
        super().__init__(**data)
        self.data = {"ping": True}


class StatusCommand(Command):
    type: CommandType = Field(default=CommandType.STATUS, frozen=True)
    
    def __init__(self, **data):
        super().__init__(**data)
        self.data = {"status": True}


class LedToggleCommand(Command):
    type: CommandType = Field(default=CommandType.LED_TOGGLE, frozen=True)
    
    def __init__(self, **data):
        super().__init__(**data)
        self.data = {"toggle": True}
