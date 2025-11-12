import json
import os
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def load_config(config_path: str) -> dict:
    """
    Loads configuration settings from a specified JSON file.

    Args:
        config_path (str): The path to the configuration file.

    Returns:
        dict: The loaded configuration settings.

    Raises:
        ValueError: If the file content is not valid JSON.
        IOError: For other reading errors.
    """
    config_path = os.path.abspath(os.path.normpath(config_path))
    if not os.path.exists(config_path):
        logger.info(f"Configuration file not found at: {config_path}. Returning empty config.")
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"Configuration loaded successfully from {config_path}")
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {config_path}: {e}")
        raise ValueError(f"Invalid JSON format in configuration file: {e}") from e
    except Exception as e:
        logger.error(f"Error reading configuration file {config_path}: {e}")
        raise IOError(f"Failed to read configuration file: {e}") from e

def save_config(settings: dict, config_path: str):
    """
    Saves current configuration settings to a JSON file.

    Args:
        settings (dict): The dictionary containing configuration settings.
        config_path (str): The path to the configuration file.

    Raises:
        IOError: If there is an error writing the file.
    """
    config_path = os.path.abspath(os.path.normpath(config_path))
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
        logger.info(f"Configuration saved successfully to {config_path}")
    except Exception as e:
        logger.error(f"Error writing configuration to {config_path}: {e}")
        raise IOError(f"Failed to save configuration file: {e}") from e
