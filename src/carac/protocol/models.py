"""
Communication protocol models for ESP32 <-> Python communication.

All messages follow the structure:
{
    "type": "message_type",
    "payload": { ... }
}

See docs/COMMUNICATION_PROTOCOL.md for complete specification.
"""
from enum import Enum
from typing import Any, Dict, Literal
import json

from pydantic import BaseModel, Field


# ============================================================================
# Message Types
# ============================================================================

class MessageType(str, Enum):
    """All valid message types in the protocol."""
    
    # Commands (App → ESP32)
    LIGHTING_SET = "lighting_set"
    PHOTO_SEQUENCE_START = "photo_sequence_start"
    MOTOR_POSITION = "motor_position"
    MOTOR_FLIP = "motor_flip"
    CAMERA_TRIGGER = "camera_trigger"
    SYSTEM_PING = "system_ping"
    SYSTEM_STATUS = "system_status"
    SYSTEM_RESET = "system_reset"
    SYSTEM_EMERGENCY_STOP = "system_emergency_stop"
    TEST_LED_TOGGLE = "test_led_toggle"
    
    # Responses (ESP32 → App)
    RESPONSE_SUCCESS = "response_success"
    RESPONSE_ERROR = "response_error"
    RESPONSE_STATUS = "response_status"
    
    # Events (ESP32 → App)
    EVENT_SEQUENCE_STARTED = "event_sequence_started"
    EVENT_SEQUENCE_PROGRESS = "event_sequence_progress"
    EVENT_SEQUENCE_COMPLETED = "event_sequence_completed"
    EVENT_SEQUENCE_STOPPED = "event_sequence_stopped"
    EVENT_ERROR = "event_error"
    EVENT_MOTOR_COMPLETE = "event_motor_complete"
    EVENT_CAMERA_TRIGGERED = "event_camera_triggered"
    EVENT_HEARTBEAT = "event_heartbeat"
    
    # Acknowledgments (ESP32 → App)
    RESPONSE_ACK = "response_ack"


class ErrorCode(str, Enum):
    """Error codes for response_error messages."""
    INVALID_CHANNEL = "INVALID_CHANNEL"
    INVALID_INTENSITY = "INVALID_INTENSITY"
    INVALID_DIRECTION = "INVALID_DIRECTION"
    MOTOR_FAULT = "MOTOR_FAULT"
    CAMERA_FAULT = "CAMERA_FAULT"
    SEQUENCE_ACTIVE = "SEQUENCE_ACTIVE"
    PARSE_ERROR = "PARSE_ERROR"
    UNKNOWN_TYPE = "UNKNOWN_TYPE"


class ConnectionStatus(str, Enum):
    """Connection state between app and ESP32."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


# ============================================================================
# Base Message Classes
# ============================================================================

class Message(BaseModel):
    """Base class for all protocol messages."""
    type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    
    def to_serial(self) -> str:
        """Serialize message to JSON string for serial transmission."""
        data = {
            "type": self.type,
            "payload": self.payload
        }
        return json.dumps(data) + "\n"
    
    @classmethod
    def from_serial(cls, data: str) -> "Message":
        """Parse message from serial JSON string."""
        try:
            if not data or not data.strip():
                return Message(
                    type=MessageType.RESPONSE_ERROR,
                    payload={
                        "message": "Empty message received",
                        "error_code": ErrorCode.PARSE_ERROR,
                        "data": {"raw": data}
                    }
                )
            
            parsed = json.loads(data.strip())
            return cls(**parsed)
        except (json.JSONDecodeError, ValueError) as e:
            return Message(
                type=MessageType.RESPONSE_ERROR,
                payload={
                    "message": f"Failed to parse message: {e}",
                    "error_code": ErrorCode.PARSE_ERROR,
                    "data": {"raw": data}
                }
            )


# ============================================================================
# Command Messages (App → ESP32)
# ============================================================================

class LightingSetCommand(Message):
    """Set lighting intensity for a specific channel."""
    
    @classmethod
    def create(cls, channel: str, intensity: int) -> "LightingSetCommand":
        return cls(
            type=MessageType.LIGHTING_SET,
            payload={"channel": channel, "intensity": intensity}
        )


class PhotoSequenceStartCommand(Message):
    """Start an automated photo sequence."""
    
    @classmethod
    def create(
        cls,
        count: int = 5,
        delay: float = 1.0,
        auto_flip: bool = False
    ) -> "PhotoSequenceStartCommand":
        return cls(
            type=MessageType.PHOTO_SEQUENCE_START,
            payload={
                "count": count,
                "delay": delay,
                "auto_flip": auto_flip
            }
        )


class MotorPositionCommand(Message):
    """Move positioning motor forward or backward."""
    
    @classmethod
    def create(
        cls,
        direction: Literal["forward", "backward"],
        steps: int | None = None
    ) -> "MotorPositionCommand":
        payload = {"direction": direction}
        if steps is not None:
            payload["steps"] = steps
        return cls(
            type=MessageType.MOTOR_POSITION,
            payload=payload
        )


class MotorFlipCommand(Message):
    """Flip the coin (reverse orientation)."""
    
    @classmethod
    def create(cls) -> "MotorFlipCommand":
        return cls(
            type=MessageType.MOTOR_FLIP,
            payload={}
        )


class CameraTriggerCommand(Message):
    """Trigger camera shutter."""
    
    @classmethod
    def create(cls, duration: int | None = None) -> "CameraTriggerCommand":
        payload = {}
        if duration is not None:
            payload["duration"] = duration
        return cls(
            type=MessageType.CAMERA_TRIGGER,
            payload=payload
        )


class SystemPingCommand(Message):
    """Ping ESP32 to check responsiveness."""
    
    @classmethod
    def create(cls) -> "SystemPingCommand":
        return cls(
            type=MessageType.SYSTEM_PING,
            payload={}
        )


class SystemStatusCommand(Message):
    """Request current system status."""
    
    @classmethod
    def create(cls) -> "SystemStatusCommand":
        return cls(
            type=MessageType.SYSTEM_STATUS,
            payload={}
        )


class SystemResetCommand(Message):
    """Reset ESP32 to initial state."""
    
    @classmethod
    def create(cls) -> "SystemResetCommand":
        return cls(
            type=MessageType.SYSTEM_RESET,
            payload={}
        )


class SystemEmergencyStopCommand(Message):
    """Emergency stop - halt all operations immediately."""
    
    @classmethod
    def create(cls) -> "SystemEmergencyStopCommand":
        return cls(
            type=MessageType.SYSTEM_EMERGENCY_STOP,
            payload={}
        )


class TestLedToggleCommand(Message):
    """Toggle built-in LED for testing."""
    
    @classmethod
    def create(cls) -> "TestLedToggleCommand":
        return cls(
            type=MessageType.TEST_LED_TOGGLE,
            payload={}
        )


# ============================================================================
# Response Messages (ESP32 → App)
# ============================================================================

class ResponseMessage(Message):
    """Base class for response messages."""
    
    def is_success(self) -> bool:
        """Check if this is a success response."""
        return self.type == MessageType.RESPONSE_SUCCESS
    
    def is_error(self) -> bool:
        """Check if this is an error response."""
        return self.type == MessageType.RESPONSE_ERROR
    
    def get_message(self) -> str:
        """Get the response message text."""
        return self.payload.get("message", "")
    
    def get_data(self) -> Dict[str, Any]:
        """Get additional response data."""
        return self.payload.get("data", {})
    
    def get_error_code(self) -> str | None:
        """Get error code (only for error responses)."""
        if self.is_error():
            return self.payload.get("error_code")
        return None


# ============================================================================
# Legacy Compatibility
# ============================================================================
# These maintain backwards compatibility with existing code

class Response(BaseModel):
    """Legacy response format for backwards compatibility."""
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def from_message(cls, msg: Message) -> "Response":
        """Convert new Message format to legacy Response format."""
        if msg.type == MessageType.RESPONSE_SUCCESS:
            return cls(
                success=True,
                message=msg.payload.get("message", "Success"),
                data=msg.payload.get("data", {})
            )
        elif msg.type == MessageType.RESPONSE_ERROR:
            return cls(
                success=False,
                message=msg.payload.get("message", "Error"),
                data=msg.payload.get("data", {})
            )
        elif msg.type == MessageType.RESPONSE_STATUS:
            return cls(
                success=True,
                message="Status retrieved",
                data=msg.payload
            )
        else:
            # For events and other messages
            return cls(
                success=True,
                message=f"Event: {msg.type}",
                data=msg.payload
            )
    
    @classmethod
    def from_serial(cls, data: str) -> "Response":
        """Parse response from serial data (legacy format)."""
        msg = Message.from_serial(data)
        return cls.from_message(msg)


# Backwards compatibility aliases
Command = Message
CommandType = MessageType  # Keep old enum name for now
PingCommand = SystemPingCommand
StatusCommand = SystemStatusCommand
LightingCommand = LightingSetCommand
PhotoSequenceCommand = PhotoSequenceStartCommand
LedToggleCommand = TestLedToggleCommand