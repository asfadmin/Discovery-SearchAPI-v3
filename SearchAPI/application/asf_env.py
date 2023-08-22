import os
import logging
import yaml
from fastapi import Request
from urllib import parse

from SearchAPI import api_logger

def load_config_file() -> dict:
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",  "maturities.yml")
    with open(file_path, "r", encoding='utf-8') as yml_file:
        config = yaml.safe_load(yml_file)
    return config

def load_config_maturity(maturity: str=None) -> dict:
    """
    Load the config for the given maturity. If 'maturity' param is None, use the MATURITY env var.
    If neither are set, default to 'local' config.
    """
    all_configs = load_config_file()
    if maturity is None:
        if 'MATURITY' in os.environ.keys():
            maturity = os.environ['MATURITY']
        else:
            api_logger.warning("os.environ['MATURITY'] not set! Defaulting to local config.")
            maturity = 'local'

    try:
        config = all_configs[maturity]
    except KeyError:
        api_logger.error(f"Invalid maturity: '{maturity}' not found in maturities.yml")
        raise
    return config
