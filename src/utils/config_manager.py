import yaml
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / '.networktools'
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / 'config.yaml'
        self.config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        return {}

    def save_config(self):
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f)

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        self.config[key] = value
        self.save_config() 