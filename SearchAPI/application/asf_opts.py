import collections
import re
from typing import Union

from fastapi import HTTPException, Request
from pydantic import ValidationError
from application.models import BaselineSearchOptsModel, SearchOptsModel

import asf_search as asf

from application.asf_env import load_config_maturity

from logger import api_logger

def string_to_range(v: Union[str, list]) -> tuple:
    if isinstance(v, list):
        return v
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
    return a

def string_to_list(v: Union[str, list[str]]) -> list:
    # v = v.replace(" ", "")
    if isinstance(v, str):
        v = v.split(",")
    return v

def parse_number_or_range(v: Union[str, list]):
    m = re.search(r'^(-?\d+(\.\d*)?)$', v)
    # If it's a digit:
    if m:
        return v
    # Else it's a range:
    return string_to_range(v)

def string_to_num_or_range_list(v: Union[str, list]):
    if isinstance(v, list):
        return v

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
    # asf.validators.parse_linestring:            string_to_list,
    # asf.validators.parse_point:                 string_to_list,

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
    LOOK_DIRECTIONS = {
        'R': 'R',
        'L': 'L'
    }
    """
    legacy SearchAPI keys that have new names in asf-search
    """

    def __init__(self):
        # This sets self.data:
        super().__init__(asf.validator_map)
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

async def get_body(request: Request):
    """
    Can remove
    """
    if (content_type := request.headers.get('content-type')) is not None:
        try:
            if content_type == 'application/json':
                data = await request.json()
                return data
            elif content_type in ['application/x-www-form-urlencoded', 'multipart/form-data']:
                data = await request.form()
                return dict(data)
        except Exception as exc:
            raise HTTPException(detail=repr(exc), status_code=400) from exc
    return {}

async def process_search_request(request: Request) -> SearchOptsModel:
    """
    Extracts the request's query+body params, returns ASFSearchOptions, request method, output format, and a dictionary
    of the merged request args wrapped in a pydantic model (SearchOptsModel)
    This entire process can be avoided once ASFSearchOptions uses pydantic's BaseModel as a class,
    then it's a matter of using @model_validator to pre-process stringified lists
    """

    query_params = dict(request.query_params)
    query_opts = get_asf_opts(dict(request.query_params))

    body = await get_body(request)
    body_opts = get_asf_opts(body)

    query_opts.merge_args(**dict(body_opts))

    merged_args = {**query_params, **body}

    if (token := merged_args.get('cmr_token')):
        session = asf.ASFSession()
        session.headers.update({'Authorization': 'Bearer {0}'.format(token)})
        query_opts.session = session

    output = merged_args.get('output', 'metalink')
    maturity = merged_args.get('maturity', 'prod')
    config = load_config_maturity(maturity=maturity)
    query_opts.host = config['cmr_base']

    try:
        # we are no longer allowing unbounded searches
        if query_opts.granule_list is None and query_opts.product_list is None:
            if query_opts.maxResults is None:
                query_opts.maxResults = asf.search_count(opts=query_opts)
            elif query_opts.maxResults <= 0:
                raise ValueError(f'Search keyword "maxResults" must be greater than 0')

            query_opts.maxResults = min(1500, query_opts.maxResults)

        searchOpts = SearchOptsModel(opts=query_opts, output=output, merged_args=merged_args, request_method=request.method)
    except (ValueError, ValidationError) as exc:
        raise HTTPException(detail=repr(exc), status_code=400) from exc

    return searchOpts

async def process_baseline_request(request: Request) -> BaselineSearchOptsModel:
    """Processes request to baseline endpoint"""
    searchOpts = await process_search_request(request=request)
    reference = searchOpts.merged_args.get('reference')
    try:
        baselineSearchOpts = BaselineSearchOptsModel(**searchOpts.model_dump(), reference=reference)
    except (ValueError, ValidationError) as exc:
        raise HTTPException(detail=repr(exc), status_code=400) from exc

    return baselineSearchOpts

def get_asf_opts(params: dict) -> asf.ASFSearchOptions:
    """
    Parses ASFSearchOptions from a dictionary
    """
    try:
        for param, value in params.items():
            if value is None or ((isinstance(value, str) or isinstance(value, list)) and len(value) == 0):
                raise ValueError(f'Empty value passed to search keyword "{param}"')
    except ValueError as exc:
        raise HTTPException(detail=repr(exc), status_code=400) from exc

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
            try:
                if validator_method in string_to_obj_map:
                    params[k] = string_to_obj_map[validator_method](v)
            except ValueError as exc:
                raise HTTPException(detail=repr(exc), status_code=400) from exc

    ### SearchOpts doesn't know how to handle these keys, but other methods need them
    # (We still want to throw on any UNKNOWN keys)
    ignore_keys_lower = ["output", "reference", "maturity", "cmr_keywords", "cmr_token"]
    params = {k: params[k] for k in params.keys() if k.lower() not in ignore_keys_lower}


    try:
        if "granule_list" in params or "product_list" in params:
            if len([param for param in params if param not in ["collections", "maxResults"]]) > 1:
                raise ValueError(f'Cannot use search keywords "granule_list/product_list" with other search params')

        if (flight_direction := params.get('flightDirection')) is not None:
            if isinstance(flight_direction, str) and len(flight_direction):
                params['flightDirection'] = ValidatorMap.FLIGHT_DIRECTIONS.get(flight_direction.upper()[0], None)
                if params['flightDirection'] is None:
                    raise ValueError(f'Invalid value passed to search keyword "flightDirection": "{flight_direction}". Valid directions are "ASCENDING" or "DESCENDING"')
        if (lookDirection := params.get('lookDirection')) is not None:
            if isinstance(lookDirection, str) and len(lookDirection):
                params['lookDirection'] = ValidatorMap.LOOK_DIRECTIONS.get(lookDirection.upper()[0], None)
                if params['lookDirection'] is None:
                    raise ValueError(f'Invalid value passed to search keyword "lookDirection": "{lookDirection}". Valid directions are "R" or "L"')
    except ValueError as exc:
        raise HTTPException(detail=repr(exc), status_code=400) from exc


    # assumes passed token is valid. May want to consider running auth_with_token(), or try passing request cookiejar??
    try:
        opts = asf.ASFSearchOptions(**params)

    except (KeyError, ValueError) as exc:
        raise HTTPException(detail=repr(exc), status_code=400) from exc
    api_logger.debug(f"asf.ASFSearchOptions object constructed: {opts})")

    return opts
