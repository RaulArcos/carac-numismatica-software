import serial.tools.list_ports
from typing import List, Optional

from loguru import logger


def get_available_ports() -> List[str]:
    try:
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        logger.debug(f"Found {len(port_list)} serial ports: {port_list}")
        return port_list
    except Exception as e:
        logger.error(f"Error detecting serial ports: {e}")
        return []


def get_port_info(port: str) -> Optional[dict]:
    try:
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if p.device == port:
                return {
                    "device": p.device,
                    "name": p.name,
                    "description": p.description,
                    "hwid": p.hwid,
                    "vid": p.vid,
                    "pid": p.pid,
                    "manufacturer": p.manufacturer,
                    "product": p.product,
                }
        return None
    except Exception as e:
        logger.error(f"Error getting port info for {port}: {e}")
        return None


def is_arduino_port(port: str) -> bool:
    info = get_port_info(port)
    if not info:
        return False
    
    arduino_indicators = [
        "arduino",
        "ch340",
        "cp210",
        "ftdi",
        "usb serial",
    ]
    
    description = info.get("description", "").lower() if info.get("description") else ""
    manufacturer = info.get("manufacturer", "").lower() if info.get("manufacturer") else ""
    product = info.get("product", "").lower() if info.get("product") else ""
    
    for indicator in arduino_indicators:
        if (indicator in description or 
            indicator in manufacturer or 
            indicator in product):
            return True
    
    return False


def get_arduino_ports() -> List[str]:
    all_ports = get_available_ports()
    arduino_ports = [port for port in all_ports if is_arduino_port(port)]
    logger.info(f"Found {len(arduino_ports)} Arduino ports: {arduino_ports}")
    return arduino_ports
