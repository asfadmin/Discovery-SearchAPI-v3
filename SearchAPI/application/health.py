import requests
import logging
import json

from .asf_env import get_config

def get_cmr_health():
    cfg = get_config()
    try:
        r = requests.get(cfg['cmr_base'] + cfg['cmr_health'], timeout=10)
        d = {'host': cfg['cmr_base'], 'health': json.loads(r.text)}
    except Exception as exc:
        logging.debug(repr(exc))
        d = {
            'host': cfg['cmr_base'],
            'error': {
                'display': 'ASF is experiencing errors loading data.  Please try again later.',
                'raw': repr(exc)
            }
        }
    return d
