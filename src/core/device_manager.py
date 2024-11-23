from typing import List, Optional
from .device import Device
from .connector import create_connection
from src.utils.csv_handler import load_devices_from_csv
from src.utils.threader import run_threaded_operation
import re

class DeviceManager:
    DEVICE_TYPE_PATTERNS = [
        # Catalyst 9000 Series (IOS-XE)
        (r'^c9[0-9]+', 'cisco_ios_xe'),    # C9200, C9300, C9400, C9500, C9600
        
        # Catalyst 3000 Series (IOS-XE)
        (r'^c3[68][0-9]+', 'cisco_ios_xe'), # C3650, C3850
        
        # ISR/ASR Routers (IOS-XE)
        (r'^(isr4|asr10[0-9]+)', 'cisco_ios_xe'),
        
        # Nexus Series (NX-OS)
        (r'^n(3|5|7|9)k', 'cisco_nxos'),
        
        # Legacy Catalyst (IOS)
        (r'^(c2[69][0-9]+|c3560)', 'cisco_ios'),  # C2960, C3560
        
        # ASA Firewalls
        (r'^asa', 'cisco_asa'),
        
        # Wireless Controllers
        (r'^(air-ct|c9800)', 'cisco_wlc'),
    ]
    
    NETMIKO_TYPE_MAP = {
        'cisco_ios_xe': 'cisco_xe',
        'cisco_ios': 'cisco_ios',
        'cisco_nxos': 'cisco_nxos',
        'cisco_asa': 'cisco_asa',
        'cisco_wlc': 'cisco_wlc'
    }
    DEFAULT_TYPE = 'cisco_ios'

    def __init__(self):
        self.devices: List[Device] = []

    def load_from_csv(self, filepath: str) -> List[Device]:
        device_data = load_devices_from_csv(filepath)
        self.devices = []
        
        for data in device_data:
            # Get model from either 'model' or 'device_model' column, default to empty string
            model = data.get('model', data.get('device_model', ''))
            
            device = Device(
                hostname=data['hostname'],
                ip=data['ip'],
                device_type=self._detect_device_type(model)
            )
            self.devices.append(device)
        return self.devices

    def connect_devices(self, selected_devices: List[Device]) -> List[Device]:
        def connect_device(device: Device):
            device_params = {
                'device_type': self.NETMIKO_TYPE_MAP.get(device.device_type, 'cisco_ios'),
                'ip': device.ip,
                'username': device.username,
                'password': device.password,
            }
            device.connection = create_connection(device_params)
            return device

        return run_threaded_operation(connect_device, selected_devices)

    def get_device_by_hostname(self, hostname: str) -> Optional[Device]:
        return next((device for device in self.devices if device.hostname == hostname), None) 

    def update_device_tree(self):
        """Update the device tree in the main window"""
        if hasattr(self, 'device_tree'):
            self.device_tree.update_devices(self.devices)

    def _detect_device_type(self, model: str) -> str:
        """
        Detect Cisco device type based on model using regex patterns
        """
        model = model.lower().strip()
        for pattern, device_type in self.DEVICE_TYPE_PATTERNS:
            if re.match(pattern, model, re.IGNORECASE):
                return device_type
        return self.DEFAULT_TYPE