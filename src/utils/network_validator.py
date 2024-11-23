from ipaddress import IPv4Network, IPv4Address
from typing import List, Set
import yaml
from pathlib import Path
import os

class NetworkValidator:
    def __init__(self):
        # Get the project root directory (where main.py is located)
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / 'config'
        self.config_dir.mkdir(exist_ok=True)
        
        self.allowed_subnets: List[IPv4Network] = []
        self.protected_devices: Set[str] = set()
        self.load_network_config()

    def _create_default_config(self):
        """Create default network boundaries configuration"""
        default_config = {
            'allowed_subnets': [
                '10.0.0.0/8',      # RFC1918 Private Network
                '172.16.0.0/12',   # RFC1918 Private Network
                '192.168.0.0/16'   # RFC1918 Private Network
            ],
            'protected_devices': [
                # Example protected devices (comment out or modify as needed)
                'CORE-SW01',        # Core Switch
                'CORE-RTR01',       # Core Router
                'FIREWALL01',       # Main Firewall
                'DC-CORE-01',       # Data Center Core
                'PROD-FW-01'        # Production Firewall
            ]
        }
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True)
        
        # Write default configuration
        config_file = self.config_dir / 'network_boundaries.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
            
        # Add explanatory comments at the top of the file
        with open(config_file, 'r') as f:
            content = f.read()
        
        header = """# Network Boundaries Configuration
# 
# allowed_subnets: List of IP ranges that are safe to crawl
#   - Use CIDR notation (e.g., '192.168.1.0/24')
#   - Devices outside these ranges will be skipped
#
# protected_devices: List of devices that should not be accessed
#   - Use exact hostnames
#   - These devices will be shown in red in the network map
#   - No automatic connections will be made to these devices
#
"""
        with open(config_file, 'w') as f:
            f.write(header + content)

    def load_network_config(self):
        """Load network configuration from YAML"""
        config_file = self.config_dir / 'network_boundaries.yaml'
        
        # Create default config if it doesn't exist
        if not config_file.exists():
            self._create_default_config()
            
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            
        # Load allowed subnets
        self.allowed_subnets = [
            IPv4Network(subnet) for subnet in config.get('allowed_subnets', [])
        ]
        
        # Load protected devices
        self.protected_devices = set(config.get('protected_devices', []))

    def is_allowed(self, ip: str, hostname: str) -> tuple[bool, str]:
        """
        Check if device is allowed to be accessed
        Returns: (is_allowed, reason)
        """
        # Check if device is in protected list
        if hostname in self.protected_devices:
            return False, "Device is in protected devices list"
            
        # Check if IP is in allowed subnets
        try:
            device_ip = IPv4Address(ip)
            if not any(device_ip in subnet for subnet in self.allowed_subnets):
                return False, "IP address is outside allowed subnets"
        except ValueError as e:
            return False, f"Invalid IP address: {str(e)}"
            
        return True, "Device is allowed" 