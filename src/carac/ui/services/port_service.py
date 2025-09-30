from typing import List

from PySide6.QtCore import QThread, Signal

from ...serialio.ports import get_available_ports, get_arduino_ports


class PortRefreshThread(QThread):
    ports_updated = Signal(list)
    
    def run(self) -> None:
        ports = get_available_ports()
        self.ports_updated.emit(ports)


class PortService:
    @staticmethod
    def get_available_ports() -> List[str]:
        return get_available_ports()
    
    @staticmethod
    def get_arduino_ports() -> List[str]:
        return get_arduino_ports()
    
    @staticmethod
    def annotate_arduino_ports(ports: List[str]) -> List[str]:
        arduino_ports = get_arduino_ports()
        return [
            f"{port} (Arduino)" if port in arduino_ports else port
            for port in ports
        ]
    
    @staticmethod
    def clean_port_name(port: str) -> str:
        return port.replace(" (Arduino)", "")
