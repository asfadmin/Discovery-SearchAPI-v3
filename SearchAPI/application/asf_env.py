import os
import logging
import yaml
from fastapi import Request
from urllib import parse

def load_config_file():
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",  "maturities.yml")
    with open(file_path, "r", encoding='utf-8') as yml_file:
        config = yaml.safe_load(yml_file)
    return config

def load_config(request: Request):
    all_config = load_config_file()

    if 'MATURITY' not in os.environ.keys():
        logging.warning('os.environ[\'MATURITY\'] not set! Defaulting to local config.]')

    maturity = os.environ['MATURITY'] if 'MATURITY' in os.environ.keys() else 'local'

    config = all_config[maturity]
    request.local_values = request.keys()
    if config['flexible_maturity']:
        if 'cmr_maturity' in request.query_params:
            request.host = parse.urlparse(config['cmr_base']).netloc

    print(request.query_params)
    # if cmr_maturity 
    request.asf_config = config
    # request.asf_base_maturity = maturity

def load_maturity_config(cmr_maturity: str):
    all_config = load_config_file()
    if cmr_maturity is None:
        cmr_maturity = 'local'
    config = all_config[cmr_maturity]
    # if config['flexible_maturity']:
    return { 'host': parse.urlparse(config['cmr_base']).netloc, 'headers': config['cmr_headers']}
    
    # return "cmr.uat.earthdata.nasa.gov"

# def request_map(config: dict):
#     return {
#     'host': config['cmr_base']
#     'provider': config['cmr_provider']
#     }
def get_config():
    return load_config_file()[os.environ['MATURITY'] if 'MATURITY' in os.environ.keys() else 'local']
