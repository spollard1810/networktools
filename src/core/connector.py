from netmiko import ConnectHandler
from typing import Dict, Optional

def create_connection(device_params: Dict) -> Optional[object]:
    try:
        # Ensure we have required parameters
        required_params = ['device_type', 'ip', 'username', 'password']
        if not all(param in device_params for param in required_params):
            raise ValueError("Missing required connection parameters")
            
        # Add timeout parameters
        connection_params = {
            'device_type': device_params['device_type'],
            'host': device_params['ip'],
            'username': device_params['username'],
            'password': device_params['password'],
            'timeout': 10,  # Connection timeout in seconds
            'fast_cli': True,  # Enable fast CLI mode
            'session_timeout': 60  # Session timeout in seconds
        }
            
        connection = ConnectHandler(**connection_params)
        return connection
    except Exception as e:
        print(f"Connection failed: {e}")
        return None