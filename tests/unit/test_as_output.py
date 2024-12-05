import pytest

import asf_search as asf
from fastapi import HTTPException

from SearchAPI.application.output import make_filename, as_output


def test_make_filename():
    filename = make_filename('json')

    assert 'json' in filename


def test_json_response_types(results):
    json_types = [
        'json', 'jsonlite', 'jsonlite2',
    ]

    for result_type in json_types:
        response = as_output(results, result_type)

        assert 'content' in response
        assert 'media_type' in response
        assert 'headers' in response
        assert 'json' in response['headers']['Content-Disposition']


def test_response_types(results):
    response_types = ['geojson', 'csv', 'kml', 'metalink']

    for result_type in response_types:
        response = as_output(results, result_type)

        assert 'content' in response
        assert 'media_type' in response
        assert 'headers' in response


def test_error(results):
    bad_result_type = ''

    with pytest.raises(HTTPException):
        as_output(results, bad_result_type)


@pytest.fixture
def results():
    return asf.ASFSearchResults([])
