import serial.tools.list_ports
from loguru import logger

ARDUINO_INDICATORS = ["arduino", "ch340", "cp210", "ftdi", "usb serial"]


def get_available_ports() -> list[str]:
    try:
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        logger.debug(f"Found {len(port_list)} serial ports: {port_list}")
        return port_list
    except Exception as e:
        logger.error(f"Error detecting serial ports: {e}")
        return []


def get_port_info(port: str) -> dict[str, str | int | None] | None:
    try:
        for p in serial.tools.list_ports.comports():
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
    if not (info := get_port_info(port)):
        return False
    search_fields = [
        str(info.get("description", "")).lower(),
        str(info.get("manufacturer", "")).lower(),
        str(info.get("product", "")).lower()
    ]
    return any(indicator in field for field in search_fields for indicator in ARDUINO_INDICATORS)


def get_arduino_ports() -> list[str]:
    try:
        ports = serial.tools.list_ports.comports()
        arduino_ports = []
        
        for port in ports:
            search_text = " ".join([
                str(port.description or ""),
                str(port.manufacturer or ""),
                str(port.product or "")
            ]).lower()
            
            if any(indicator in search_text for indicator in ARDUINO_INDICATORS):
                arduino_ports.append(port.device)
        
        logger.info(f"Found {len(arduino_ports)} Arduino ports: {arduino_ports}")
        return arduino_ports
    except Exception as e:
        logger.error(f"Error detecting Arduino ports: {e}")
        return []