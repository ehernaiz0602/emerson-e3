import os
import json
import logging
import sqlite3
from typing import Any
from pathlib import Path

logger = logging.getLogger(__name__)

# DEFAULT CONFIGURATIONS
SETTINGS_AZURE = {
    "tenant_id": "",
    "client_id": "",
    "device_id": "",
    "scope_id": "",
    "secret_name": "",
    "certificate_name": "",
    "keyvault": "",
    "sas_ttl": 90,
}

SETTINGS_GENERAL = {
    "loglevel": "info",
    "logfile_maxsize_mb": 100,
    "max_offline_messages": 1_000,
    "offline_message_trimsize": 250,
    "http_retries": 3,
    "retry_delay_ms": 3_000,
    "http_timeout": 3,
    "request_delay_ms": 1_000,
    "publish_interval": 10,
    "workers": 2,
    "gui": False,
}

SETTINGS_EMERSON3 = {
    "polling_interval": 180,
    "devices": [
        {
            "name": "panel_0",
            "ip": "192.168.1.250",
        }
    ]
}

PTRS = {
    "Global Data": [
        "OatOut",
    ]
}

# Project paths
SETTINGS_DIR = Path(__file__).parent
SRC_DIR = SETTINGS_DIR.parent
PROJECT_DIR = SRC_DIR.parent

RUNTIME_DIRS = [
    PROJECT_DIR / "conf",
    PROJECT_DIR / "data",
    PROJECT_DIR / "logs",
]


def create_files():

    # Create directories if they don't exist
    for directory in RUNTIME_DIRS:
        if not Path(directory).is_dir():
            os.makedirs(directory)
            logger.debug(f"Created {str(directory)}")

    # Create conf files:
    def create_conf(name: str, conf_file: dict[str, Any]):
        this_file = RUNTIME_DIRS[0]/name
        if not Path(this_file).is_file():
            with open(this_file, "w+") as f:
                json.dump(conf_file, f, indent=2)
            logger.debug(f"Created default {name}")

    create_conf("settings_azure.json", SETTINGS_AZURE)
    create_conf("settings_general.json", SETTINGS_GENERAL)
    create_conf("settings_emerson3.json", SETTINGS_EMERSON3)
    create_conf("ptrs.json", PTRS)

    # Create database file
    with sqlite3.connect(RUNTIME_DIRS[1]/"database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages
            (timestamp text, ip text, response text, method text, processed integer)
            """
        )
        conn.commit()

    # Create jsonl log file
    logfile_path = RUNTIME_DIRS[2]/"log.jsonl"
    if not Path(logfile_path).is_file():
        with open(logfile_path, "w+") as _:
            pass
        logger.debug(f"Created log.jsonl file")

def load_files():
    def load_file(file, conf_structure):
        this_filepath = RUNTIME_DIRS[0] / file
        logging.debug(f"Attempting to load: {this_filepath}")
        with open(this_filepath) as f:
            this_conf = json.load(f)
        if this_conf.keys() == conf_structure.keys():
            logger.debug(f"Loaded {file} successfully")
            return this_conf
        logger.warning(f"Incorrect structure detected at {file}. Please verify")
        logger.warning(f"Continuing with default definition for {file}")
        return conf_structure

    settings_azure = load_file("settings_azure.json", SETTINGS_AZURE)
    settings_general = load_file("settings_general.json", SETTINGS_GENERAL)
    settings_emerson3 = load_file("settings_emerson3.json", SETTINGS_EMERSON3)

    return (settings_azure, settings_emerson3, settings_general)

def load_settings():
    create_files()
    return load_files()

# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    load_settings()
