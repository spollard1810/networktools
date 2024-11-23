from enum import Enum
from dataclasses import dataclass
from typing import Optional

class DeviceStatus(Enum):
    DISCONNECTED = "Disconnected"
    CONNECTED = "Connected"
    ERROR = "Error"
    PROTECTED = "Protected"

@dataclass
class Device:
    hostname: str
    ip: str
    device_type: str
    username: Optional[str] = None
    password: Optional[str] = None
    connection: Optional[object] = None
    status: DeviceStatus = DeviceStatus.DISCONNECTED
    
    def detect_device_type(self) -> str:
        # Logic to auto-detect device type if not specified
        return self.device_type