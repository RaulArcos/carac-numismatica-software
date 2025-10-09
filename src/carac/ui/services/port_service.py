from PySide6.QtCore import QThread, Signal

from ...serialio.ports import get_available_ports, get_arduino_ports


class PortRefreshThread(QThread):
    ports_updated = Signal(list)
    
    def run(self) -> None:
        ports = get_available_ports()
        self.ports_updated.emit(ports)


class PortService:
    ARDUINO_ANNOTATION = " (Arduino)"
    
    @classmethod
    def get_available_ports(cls) -> list[str]:
        return get_available_ports()
    
    @classmethod
    def get_arduino_ports(cls) -> list[str]:
        return get_arduino_ports()
    
    @classmethod
    def annotate_arduino_ports(cls, ports: list[str]) -> list[str]:
        arduino_ports = cls.get_arduino_ports()
        return [
            f"{port}{cls.ARDUINO_ANNOTATION}" if port in arduino_ports else port
            for port in ports
        ]
    
    @classmethod
    def clean_port_name(cls, port: str) -> str:
        return port.replace(cls.ARDUINO_ANNOTATION, "")
