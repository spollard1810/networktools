from dataclasses import dataclass
from typing import Optional

@dataclass
class Device:
    hostname: str
    ip: str
    device_type: str
    username: Optional[str] = None
    password: Optional[str] = None
    connection: Optional[object] = None
    
    def detect_device_type(self) -> str:
        # Logic to auto-detect device type if not specified
        return self.device_type