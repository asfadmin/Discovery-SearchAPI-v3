
import collections
import re
from typing import Callable

from fastapi import HTTPException, Request
import asf_search as asf

from SearchAPI import api_logger

def string_to_range(v: str) -> tuple:
    # api_logger.debug(f"string_to_range({v})")
    try:
        v = v.replace(' ', '')
        m = re.search(r'^(-?\d+(\.\d*)?)-(-?\d+(\.\d*)?)$', v)
        if m is None:
            raise ValueError(f'Invalid range: {v}')
        a = (m.group(1), m.group(3))
        if a[0] > a[1]:
            raise ValueError()
        if a[0] == a[1]:
            a = a[0]
    except ValueError as exc:
        raise ValueError(f'Invalid range: {exc}') from exc
    # api_logger.debug(f"string_to_range returning({v})")
    return a

def string_to_list(v: str) -> list:
    # v = v.replace(" ", "")
    v = v.split(",")
    return v

def parse_number_or_range(v: str):
    m = re.search(r'^(-?\d+(\.\d*)?)$', v)
    # If it's a digit:
    if m:
        return v
    # Else it's a range:
    return string_to_range(v)



def string_to_num_or_range_list(v: str):
    v_list = string_to_list(v)
    v_list = [parse_number_or_range(i) for i in v_list]
    return v_list

string_to_obj_map = {
    # Range only:
    asf.validators.parse_date_range:            string_to_range,
    asf.validators.parse_int_range:             string_to_range,
    asf.validators.parse_float_range:           string_to_range,
    # List only:
    asf.validators.parse_string_list:           string_to_list,
    asf.validators.parse_int_list:              string_to_list,
    asf.validators.parse_float_list:            string_to_list,
    # asf.validators.parse_circle:                string_to_list,
    # Number or Range-list:
    asf.validators.parse_int_or_range_list:     string_to_num_or_range_list,
    asf.validators.parse_float_or_range_list:   string_to_num_or_range_list,
}

class ValidatorMap(collections.UserDict):
    """
    For adding case-insensitive logic to the validator map, and mapping legacy keywords to ASFSearchOptions
    i.e:
        >>> v = ValidatorMap()
        >>> "maxresults" in v # True
        >>> v["mAxReSuLtS"] # Pointer to validator method
        >>> v.actual_key_case("mAxReSuLtS") # "maxResults", what asf_search expects
    """
    ALIASED_KEYWORDS = {
        'collectionname': 'campaign'
    }
    FLIGHT_DIRECTIONS = {
        'A': 'ASCENDING',
        'D': 'DESCENDING'
    }
    """
    legacy SearchAPI keys that have new names in asf-search
    """

    def __init__(self):
        # This sets self.data:
        super().__init__(asf.validator_map.validator_map)
        # value is the normalized key, key is the lower-key
        self.lower_lookup = {k.lower(): k for k in self.data.keys()}
    def __contains__(self, k) -> bool:
        return k.lower() in [*self.lower_lookup.keys(), *self.ALIASED_KEYWORDS.keys()] 
    def __getitem__(self, k):
        key = self.ALIASED_KEYWORDS.get(k.lower(), k)
        api_logger.debug(f"Keyword {key}")
        corrected_case_key = self.actual_key_case(key)
        return self.data[corrected_case_key]
    def actual_key_case(self, k):
        # This should raise keyerror if not found:
        return self.lower_lookup[k.lower()]
    def alias_params(self, params: dict) -> dict:
            return {
                self.ALIASED_KEYWORDS.get(k.lower(), k): v
                for k,v in params.items()
            }

def get_asf_opts(request: Request) -> asf.ASFSearchOptions:
    params = dict(request.query_params)

    ### If your key is in validator map, make it match case sensitivity:
    validatorMap = ValidatorMap()
    params = validatorMap.alias_params(params)
    # You have to rebuild the dict, since you can't change keys in place
    params = {
        validatorMap.actual_key_case(k)
            if k in validatorMap
            else k:v
        for k,v in params.items()
    }

    ### De-stringify the values if we know how:
    for k,v in params.items():
        if k in validatorMap:
            validator_method = validatorMap[k]
            # If the method is in our map, de-stringify it:
            if validator_method in string_to_obj_map:
                params[k] = string_to_obj_map[validator_method](v)

    ### SearchOpts doesn't know how to handle these keys, but other methods need them
    # (We still want to throw on any UNKNOWN keys)
    ignore_keys_lower = ["output", "reference", "maturity"]
    params = {k: params[k] for k in params.keys() if k.lower() not in ignore_keys_lower}
    
    if flight_direction := params.get('flightDirection') is not None:
        if isinstance(flight_direction, str) and len(flight_direction):
            params['flightDirection'] = ValidatorMap.FLIGHT_DIRECTIONS.get(flight_direction[0], flight_direction)
    try:
        opts = asf.ASFSearchOptions(**params)
    except (KeyError, ValueError) as exc:
        raise HTTPException(detail=repr(exc), status_code=400) from exc
    api_logger.debug(f"asf.ASFSearchOptions object constructed: {opts})")
    return opts
