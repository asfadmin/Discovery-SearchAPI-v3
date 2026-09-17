import pytest
from fastapi import HTTPException

from SearchAPI.application.asf_opts import get_asf_opts, string_to_bool


def test_string_to_bool():
    assert string_to_bool('true') is True
    assert string_to_bool('False') is False
    assert string_to_bool(True) is True

    with pytest.raises(ValueError):
        string_to_bool('asdf')


def test_bool_keywords_from_strings():
    assert get_asf_opts({'jointObservation': 'true'}).jointObservation is True
    assert get_asf_opts({'jointObservation': 'false'}).jointObservation is False
    assert get_asf_opts({'collectionAlias': 'false'}).collectionAlias is False


def test_invalid_bool_keyword_is_400():
    with pytest.raises(HTTPException) as exc:
        get_asf_opts({'jointObservation': 'asdf'})

    assert exc.value.status_code == 400
