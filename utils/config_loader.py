"""Configuration loader utility."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file with environment variable overrides.
    
    Args:
        config_path: Path to config YAML file
    
    Returns:
        Configuration dictionary
    """
    default_config = {
        "excel_path": "data/employees_mcp.xlsx",
        "openai": {
            "model": "gpt-4o-mini",
            "temperature": 0,
            "max_retries": 3,
            "retry_delay": 2
        },
        "processing": {
            "batch_size": 10,
            "backup_before_update": True,
            "backup_directory": "backups"
        },
        "logging": {
            "level": "INFO",
            "file": "logs/mcp_server.log",
            "console": True
        },
        "rules": {
            "designation": {
                "intern_max_years": 2,
                "junior_max_years": 4,
                "senior_max_years": 7,
                "lead_min_years": 8
            },
            "salary_band": {
                "l1_max_years": 3,
                "l2_max_years": 6,
                "l3_min_years": 7
            }
        }
    }
    
    config_file = Path(config_path)
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f) or {}
                # Merge with defaults
                config = _merge_dicts(default_config, file_config)
        except Exception as e:
            print(f"Warning: Could not load config file {config_path}: {e}")
            config = default_config
    else:
        config = default_config
    
    # Override with environment variables
    if os.getenv("EXCEL_PATH"):
        config["excel_path"] = os.getenv("EXCEL_PATH")
    if os.getenv("OPENAI_MODEL"):
        config["openai"]["model"] = os.getenv("OPENAI_MODEL")
    
    return config


def _merge_dicts(base: Dict, override: Dict) -> Dict:
    """Recursively merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result

