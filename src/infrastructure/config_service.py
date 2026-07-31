import yaml
from pathlib import Path
from typing import Any, Dict

class ConfigService:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigService, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        config_path = Path(__file__).parent.parent.parent / 'config' / 'thresholds.yaml'
        if not config_path.exists():
            # Fallback for different execution contexts
            config_path = Path.cwd() / 'config' / 'thresholds.yaml'
            
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        else:
            print(f"Warning: Config file not found at {config_path}")

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get config value using dot notation (e.g., 'ai.yolo.confidence_threshold')
        """
        keys = key_path.split('.')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

# Global instance
config_service = ConfigService()
