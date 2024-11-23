# NETWORKTOOLS
# Networking toolkit for internal use

## File Structure

## Features
- load devices from csv button to import (headers: hostname, ip, device_type)
- initialize device list, creating device objects (automatically detects device type)
- use netmiko to connect to devices when needed
- create a thread for each device
- 'device list'
- 'vlan discovery'
- 'network discovery'
- 'local routes'
-  'audit'
- 'reports'
- 'crawler'

- Tkinter GUI
- threading

from dataclasses import dataclass
from typing import Optional

@dataclass
class Device:
    hostname: str
    ip: str
    device_type: str
    connection: Optional[object] = None
    
    def detect_device_type(self) -> str:
        # Logic to auto-detect device type if not specified
        return self.device_type

