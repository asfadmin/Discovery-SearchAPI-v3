import pytest
import requests
from tenacity import wait_none


from SearchAPI.application.health import get_cmr_health, _query_cmr_health
from SearchAPI.application.asf_env import load_config_maturity


_query_cmr_health.retry.wait = wait_none()


def test_health(requests_mock, cfg):
    base, endpoint = cfg['cmr_base'], cfg['cmr_health']
    requests_mock.get(f'https://{base}{endpoint}', text='{}')

    health_resp = get_cmr_health(cfg['cmr_base'], cfg['cmr_health'])

    assert 'health' in health_resp
    assert 'host' in health_resp


def test_error_catching(requests_mock, cfg):
    base, endpoint = cfg['cmr_base'], cfg['cmr_health']
    requests_mock.register_uri('GET', f'https://{base}{endpoint}', exc=requests.exceptions.ConnectTimeout)

    health_resp = get_cmr_health(cfg['cmr_base'], cfg['cmr_health'])

    assert 'error' in health_resp


@pytest.fixture
def cfg():
    return load_config_maturity('local')
