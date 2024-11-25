import requests
from typing import List
from ipaddress import IPv4Network
import logging

class MicetroClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.auth = (username, password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.logger = logging.getLogger(__name__)

    def get_networks(self) -> List[IPv4Network]:
        """
        Fetch all networks from Micetro (READ-ONLY operation)
        Returns: List of IPv4Network objects
        """
        endpoint = f"{self.base_url}/api/v1/ranges"
        try:
            # Explicitly use GET method for read-only operation
            response = self.session.get(
                endpoint,
                timeout=30,
                verify=True  # Ensure SSL verification
            )
            response.raise_for_status()
            
            networks = []
            for network in response.json().get('result', []):
                try:
                    net = IPv4Network(f"{network['from']}/{network['netmask']}")
                    networks.append(net)
                except ValueError as e:
                    self.logger.warning(f"Skipping invalid network: {e}")
            
            return networks
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching networks from Micetro: {e}")
            raise 