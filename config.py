import json
import logging
import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

load_dotenv()

_temp_logger = logging.getLogger("config_init")
if not _temp_logger.handlers:
    _temp_logger.addHandler(logging.StreamHandler())
    _temp_logger.setLevel(logging.WARNING)
    _temp_logger.info("Temporary logger initialized for config loading")


class Config:
    def __init__(self):
        self.APP_NAME = os.getenv("BASE__APP_NAME", "dhr-download-stac-relay")

        self.logger = _temp_logger

        # ----------
        # LOGGING
        # ----------
        self.LOG_LEVEL = int(os.getenv("LOGGER__LOG_LEVEL", "20"))

        log_dir_raw = os.getenv("LOGGER__LOG_DIRECTORY", "./log")
        if not os.path.isabs(log_dir_raw):
            self.LOG_DIR = Path.cwd() / log_dir_raw
        else:
            self.LOG_DIR = Path(log_dir_raw)

        self.LOG_FILE = os.getenv("LOGGER__LOG_FILENAME") or f"{self.APP_NAME}.log"

        # ----------
        # SANIC
        # ----------
        self.SANIC_HOST = os.getenv("SANIC__SERVER_HOST", "0.0.0.0")
        try:
            self.SANIC_PORT = int(os.getenv("SANIC__SERVER_PORT", "8080"))
        except ValueError:
            self.logger.error("Invalid SANIC__SERVER_PORT value, defaulting to 8080")
            self.SANIC_PORT = 8080

        # --- SANIC BASIC AUTH CONFIGURATION  ---
        self._AUTH_CONFIGS: Dict[str, Dict[str, str]] = {}
        self._load_auth_configs()

        # ----------
        # S3
        # ----------
        self._S3_CONFIGS: Dict[str, Dict[str, str]] = {}
        self._load_s3_services()

    def _load_auth_configs(self):
        """
        Loads SANIC Basic auth from .env JSON string
        """

        raw = os.getenv("SANIC_AUTH_CONFIG", "{}")

        try:
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                raise ValueError("SANIC_AUTH_CONFIG must be a JSON object")

            self._AUTH_CONFIGS = parsed

            for scope_name in self._AUTH_CONFIGS:
                count = len(self._AUTH_CONFIGS[scope_name])
                self.logger.info(f"Loaded auth scope '{scope_name}' with {count} users.")

        except Exception as e:
            self.logger.error(f"Failed to parse SANIC_AUTH_CONFIG: {e}")
            self._AUTH_CONFIGS = {}

    def _load_s3_services(self):
        """
        Loads S3 services config from .env JSON string
        """

        raw = os.getenv("S3_SERVICES", "{}")

        try:
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                raise ValueError("S3_SERVICES must be a JSON object")

            # Key validation & normalization
            for service_name, cfg in parsed.items():
                key = service_name.lower()

                required_keys = ["host_base", "host_bucket", "access_key", "secret_key"]
                missing = [k for k in required_keys if k not in cfg]

                if missing:
                    self.logger.warning(f"S3 service '{key}' is missing fields: {missing}")

                self._S3_CONFIGS[key] = cfg
                self.logger.info(f"Loaded S3 service: '{key}'")

        except Exception as e:
            self.logger.error(f"Failed to parse S3_SERVICES: {e}")
            self._S3_CONFIGS = {}

    def get_auth_users(self, scope_name: str) -> Dict[str, str]:
        return self._AUTH_CONFIGS.get(scope_name.lower(), {})

    def get_s3_config(self, service_name: str) -> Dict[str, str]:
        return self._S3_CONFIGS.get(service_name.lower(), {})


# Singleton instance
config = Config()
