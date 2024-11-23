import hashlib
import json
import os
from typing import Optional, Dict
from pathlib import Path

class CredentialsManager:
    def __init__(self):
        self.config_dir = Path.home() / '.networktools'
        self.credentials_file = self.config_dir / 'credentials.json'
        self._ensure_config_dir()
        self.credentials: Dict = self._load_credentials()

    def _ensure_config_dir(self):
        """Ensure configuration directory exists"""
        self.config_dir.mkdir(exist_ok=True)

    def _load_credentials(self) -> Dict:
        """Load saved credentials if they exist"""
        if self.credentials_file.exists():
            with open(self.credentials_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_credentials(self):
        """Save credentials to file"""
        with open(self.credentials_file, 'w') as f:
            json.dump(self.credentials, f)

    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def save_tacacs_credentials(self, username: str, password: str):
        """Save TACACS credentials"""
        self.credentials['tacacs'] = {
            'username': username,
            'password': self.hash_password(password)
        }
        self._save_credentials()

    def get_tacacs_credentials(self) -> Optional[Dict[str, str]]:
        """Get saved TACACS credentials"""
        return self.credentials.get('tacacs')

    def clear_credentials(self):
        """Clear all saved credentials"""
        self.credentials = {}
        self._save_credentials() 