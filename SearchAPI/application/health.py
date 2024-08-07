import requests
import logging
import json

from .asf_env import load_config_maturity
from tenacity import retry, stop_after_attempt, wait_fixed

def get_cmr_health():
    cfg = load_config_maturity()
    cmr_base = cfg['cmr_base']
    health_endpoint = cfg['cmr_health']
    try:
        cmr_health_response = _query_cmr_health(cmr_base=cmr_base, health_endpoint=health_endpoint)
    except Exception as exc:
        logging.debug(repr(exc))
        cmr_health_response = {
            'host': cmr_base,
            'error': {
                'display': 'ASF is experiencing errors loading data.  Please try again later.',
                'raw': repr(exc)
            }
        }
        
    return cmr_health_response

@retry(stop=stop_after_attempt(3), wait=wait_fixed(3), reraise=True)
def _query_cmr_health(cmr_base: str, health_endpoint: str):
    r = requests.get(f'https://{cmr_base}{health_endpoint}', timeout=10)
    r.raise_for_status()
    return {'host': cmr_base, 'health': r.json()}
