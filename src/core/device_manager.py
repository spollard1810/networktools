from typing import List, Optional
from .device import Device
from .connector import create_connection
from src.utils.csv_handler import load_devices_from_csv
from src.utils.threader import run_threaded_operation

class DeviceManager:
    def __init__(self):
        self.devices: List[Device] = []

    def load_from_csv(self, filepath: str) -> List[Device]:
        device_data = load_devices_from_csv(filepath)
        self.devices = []
        
        for data in device_data:
            device = Device(
                hostname=data['hostname'],
                ip=data['ip'],
                device_type=data['device_type']
            )
            self.devices.append(device)
        return self.devices

    def connect_devices(self, selected_devices: List[Device]) -> List[Device]:
        def connect_device(device: Device):
            device_params = {
                'device_type': device.device_type,
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