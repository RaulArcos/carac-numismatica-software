import json
from enum import Enum
from typing import Any, Dict, Literal

from pydantic import BaseModel, Field


class MessageType(str, Enum):
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
    RESPONSE_SUCCESS = "response_success"
    RESPONSE_ERROR = "response_error"
    RESPONSE_STATUS = "response_status"
    EVENT_SEQUENCE_STARTED = "event_sequence_started"
    EVENT_SEQUENCE_PROGRESS = "event_sequence_progress"
    EVENT_SEQUENCE_COMPLETED = "event_sequence_completed"
    EVENT_SEQUENCE_STOPPED = "event_sequence_stopped"
    EVENT_ERROR = "event_error"
    EVENT_MOTOR_COMPLETE = "event_motor_complete"
    EVENT_CAMERA_TRIGGERED = "event_camera_triggered"
    EVENT_HEARTBEAT = "event_heartbeat"
    RESPONSE_ACK = "response_ack"


class ErrorCode(str, Enum):
    INVALID_CHANNEL = "INVALID_CHANNEL"
    INVALID_INTENSITY = "INVALID_INTENSITY"
    INVALID_DIRECTION = "INVALID_DIRECTION"
    MOTOR_FAULT = "MOTOR_FAULT"
    CAMERA_FAULT = "CAMERA_FAULT"
    SEQUENCE_ACTIVE = "SEQUENCE_ACTIVE"
    PARSE_ERROR = "PARSE_ERROR"
    UNKNOWN_TYPE = "UNKNOWN_TYPE"


class ConnectionStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class Message(BaseModel):
    type: str
    payload: Dict[str, Any] = Field(default_factory=dict)

    def to_serial(self) -> str:
        data = {"type": self.type, "payload": self.payload}
        return json.dumps(data) + "\n"

    @classmethod
    def from_serial(cls, data: str) -> "Message":
        try:
            if not data or not data.strip():
                return cls._create_parse_error("Empty message received", data)

            parsed = json.loads(data.strip())
            return cls(**parsed)
        except (json.JSONDecodeError, ValueError) as e:
            return cls._create_parse_error(f"Failed to parse message: {e}", data)

    @classmethod
    def _create_parse_error(cls, message: str, raw_data: str) -> "Message":
        return Message(
            type=MessageType.RESPONSE_ERROR,
            payload={
                "message": message,
                "error_code": ErrorCode.PARSE_ERROR,
                "data": {"raw": raw_data}
            }
        )


class LightingSetCommand(Message):
    @classmethod
    def create(cls, channel: str, intensity: int) -> "LightingSetCommand":
        return cls(
            type=MessageType.LIGHTING_SET,
            payload={"channel": channel, "intensity": intensity}
        )


class PhotoSequenceStartCommand(Message):
    @classmethod
    def create(
        cls,
        count: int = 5,
        delay: float = 1.0,
        auto_flip: bool = False
    ) -> "PhotoSequenceStartCommand":
        return cls(
            type=MessageType.PHOTO_SEQUENCE_START,
            payload={"count": count, "delay": delay, "auto_flip": auto_flip}
        )


class MotorPositionCommand(Message):
    @classmethod
    def create(
        cls,
        direction: Literal["forward", "backward"],
        steps: int | None = None
    ) -> "MotorPositionCommand":
        payload = {"direction": direction}
        if steps is not None:
            payload["steps"] = steps
        return cls(type=MessageType.MOTOR_POSITION, payload=payload)


class MotorFlipCommand(Message):
    @classmethod
    def create(cls) -> "MotorFlipCommand":
        return cls(type=MessageType.MOTOR_FLIP, payload={})


class CameraTriggerCommand(Message):
    @classmethod
    def create(cls, duration: int | None = None) -> "CameraTriggerCommand":
        payload = {}
        if duration is not None:
            payload["duration"] = duration
        return cls(type=MessageType.CAMERA_TRIGGER, payload=payload)


class SystemPingCommand(Message):
    @classmethod
    def create(cls) -> "SystemPingCommand":
        return cls(type=MessageType.SYSTEM_PING, payload={})


class SystemStatusCommand(Message):
    @classmethod
    def create(cls) -> "SystemStatusCommand":
        return cls(type=MessageType.SYSTEM_STATUS, payload={})


class SystemResetCommand(Message):
    @classmethod
    def create(cls) -> "SystemResetCommand":
        return cls(type=MessageType.SYSTEM_RESET, payload={})


class SystemEmergencyStopCommand(Message):
    @classmethod
    def create(cls) -> "SystemEmergencyStopCommand":
        return cls(type=MessageType.SYSTEM_EMERGENCY_STOP, payload={})


class TestLedToggleCommand(Message):
    @classmethod
    def create(cls) -> "TestLedToggleCommand":
        return cls(type=MessageType.TEST_LED_TOGGLE, payload={})


class ResponseMessage(Message):
    def is_success(self) -> bool:
        return self.type == MessageType.RESPONSE_SUCCESS

    def is_error(self) -> bool:
        return self.type == MessageType.RESPONSE_ERROR

    def get_message(self) -> str:
        return self.payload.get("message", "")

    def get_data(self) -> Dict[str, Any]:
        return self.payload.get("data", {})

    def get_error_code(self) -> str | None:
        if self.is_error():
            return self.payload.get("error_code")
        return None


class Response(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_message(cls, msg: Message) -> "Response":
        response_map = {
            MessageType.RESPONSE_SUCCESS: lambda: cls(
                success=True,
                message=msg.payload.get("message", "Success"),
                data=msg.payload.get("data", {})
            ),
            MessageType.RESPONSE_ERROR: lambda: cls(
                success=False,
                message=msg.payload.get("message", "Error"),
                data=msg.payload.get("data", {})
            ),
            MessageType.RESPONSE_STATUS: lambda: cls(
                success=True,
                message="Status retrieved",
                data=msg.payload
            ),
        }

        return response_map.get(
            msg.type,
            lambda: cls(
                success=True,
                message=f"Event: {msg.type}",
                data=msg.payload
            )
        )()

    @classmethod
    def from_serial(cls, data: str) -> "Response":
        msg = Message.from_serial(data)
        return cls.from_message(msg)


Command = Message
CommandType = MessageType
PingCommand = SystemPingCommand
StatusCommand = SystemStatusCommand
LightingCommand = LightingSetCommand
PhotoSequenceCommand = PhotoSequenceStartCommand
LedToggleCommand = TestLedToggleCommand