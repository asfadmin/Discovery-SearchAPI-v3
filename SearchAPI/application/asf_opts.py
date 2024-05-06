
import collections
import datetime
import re
from typing import Callable, ClassVar, Optional, Sequence, Tuple, Type, Union
from typing_extensions import Annotated
from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, InstanceOf, BeforeValidator, PlainValidator, AliasPath
import asf_search as asf
from .asf_env import load_config_maturity

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
    if isinstance(v, str) and ',' in v:
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
    asf.validators.parse_circle:                string_to_list,
    asf.validators.parse_linestring:            string_to_list,
    asf.validators.parse_point:                 string_to_list,
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

class APIParamsModel(BaseModel):
    opts: InstanceOf[asf.ASFSearchOptions] = asf.ASFSearchOptions()
    output: str = 'metalink',
    # body: dict = {}

class BaselinAPIParamsModel(APIParamsModel):
    reference: str

async def get_baseline_asf_opts(request: Request) -> BaselinAPIParamsModel:
    params = dict(request.query_params)
    base_opts = get_asf_opts(request=request)
    

def get_asf_opts(request: Request) -> APIParamsModel:
    params = dict(request.query_params)
    try:
        for param, value in params.items():
            if len(value) == 0:
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
    
    maturity = params.get('maturity')
    

    config = load_config_maturity(maturity=maturity)
    params['host'] = config['cmr_base']
    
    # assumes passed token is valid. May want to consider running auth_with_token(), or try passing request cookiejar??
    if (token := params.get('cmr_token')):
        session = asf.ASFSession()
        session.headers.update({'Authorization': 'Bearer {0}'.format(token)})
        params['session'] =  session
    try:
        opts = asf.ASFSearchOptions(**params)

        # we are no longer allowing unbounded searches
        if opts.granule_list is None and opts.product_list is None:
            if opts.maxResults is None:
                opts.maxResults = asf.search_count(opts=opts)
            elif opts.maxResults <= 0:
                raise ValueError(f'Search keyword "maxResults" must be greater than 0')
        
            opts.maxResults = min(1500, opts.maxResults)
    
    except (KeyError, ValueError) as exc:
        raise HTTPException(detail=repr(exc), status_code=400) from exc
    api_logger.debug(f"asf.ASFSearchOptions object constructed: {opts})")
    # return opts
    return APIParamsModel(opts=opts, output=params.get('output', 'metalink'))


class WKTModel(BaseModel):
    wkt: str = Field(default='')



int_range_or_list = Annotated[
    Optional[Union[int, Tuple[int, int], Sequence[Union[int, Tuple[int, int]]]]],
    PlainValidator(asf.validators.parse_int_or_range_list), 
    BeforeValidator(string_to_num_or_range_list)]

float_range_or_list = Annotated[
    Optional[Union[int, Tuple[float, float], Sequence[Union[float, Tuple[float, float]]]]],
    PlainValidator(asf.validators.parse_float_or_range_list), 
    BeforeValidator(string_to_num_or_range_list)]

string_list = Annotated[
    Optional[Union[str, Sequence[str]]], 
    PlainValidator(asf.validators.parse_string_list),
    BeforeValidator(string_to_list)]

int_list = Annotated[
    Optional[Union[int, Sequence[int]]],
    PlainValidator(asf.validators.parse_int_list),
    BeforeValidator(string_to_list)
]

float_list = Annotated[
    Optional[Union[float, Sequence[float]]],
    PlainValidator(asf.validators.parse_float_list),
    BeforeValidator(string_to_list)
]

cirle_type = Annotated[
    Optional[Tuple[float, float, float]],
    PlainValidator(asf.validators.parse_circle),
    BeforeValidator(string_to_list)
]

linestring_type = Annotated[
    Optional[Sequence[float]],
    PlainValidator(asf.validators.parse_linestring),
    BeforeValidator(string_to_list)
]

point_type = Annotated[
    Optional[Sequence[float]],
    PlainValidator(asf.validators.parse_point),
    BeforeValidator(string_to_list)
]

class ParamsModel(asf.ASFSearchOptions):
    absoluteOrbit: int_range_or_list = None
    asfFrame: int_range_or_list = None
    beamMode: string_list = None
    beamSwath: string_list = None
    campaign: string_list = None # Field(validation_alias=AliasPath('collectionname', None))
    circle:  cirle_type = None
    linestring: linestring_type = None
    maxDoppler: Optional[float] = None
    minDoppler: Optional[float] = None
    end: Optional[Union[datetime.datetime, str]] = None
    maxFaradayRotation: Optional[float] = None
    minFaradayRotation: Optional[float] = None
    flightDirection: Optional[str] = None
    flightLine: Optional[str] = None
    frame: int_range_or_list = None
    granule_list: string_list = None
    groupID: string_list = None
    insarStackId: Optional[str] = None
    instrument: string_list = None
    intersectsWith: Optional[str] = None
    lookDirection: string_list = None
    offNadirAngle: float_range_or_list = None
    platform: string_list = None
    polarization: string_list = None
    processingDate: Optional[Union[datetime.datetime, str]] = None
    processingLevel: string_list = None
    product_list: string_list = None
    relativeOrbit: int_range_or_list = None
    season: int_list = None
    start: Union[datetime.datetime, str] = None
    absoluteBurstID: int_list = None
    relativeBurstID: int_list = None
    fullBurstID: string_list = None
    collections: string_list = None
    temporalBaselineDays: string_list = None
    operaBurstID: string_list = None
    dataset: string_list = None
    shortName: string_list = None
    output: str = 'metalink'
    maturity: Optional[str] = None
    cmr_token: Optional[str] = None
    maxResults: Optional[int] = Field(..., gt=0)
    
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    
    excluded_fields: ClassVar[list[str]] = ['cmr_token', 'maturity', 'output']

    def get_opts(self) -> asf.ASFSearchOptions:

        if self.granule_list is None and self.product_list is None:
            if self.maxResults is None:
                self.maxResults = 1500
            elif self.maxResults <= 0:
                raise ValueError(f'Search keyword "maxResults" must be greater than 0')
        
        
        config = load_config_maturity(maturity=self.maturity)
        host = config['cmr_base']

        session = asf.ASFSession(cmr_host=host)
        # assumes passed token is valid. May want to consider running auth_with_token(), or try passing request cookiejar??
        if self.cmr_token is not None:
            session.auth_with_token(self.cmr_token)
            # session.headers.update({'Authorization': 'Bearer {0}'.format(token)})
        
        dict_opts = self._get_search_options_dict()
        try:
            opts = asf.ASFSearchOptions(**dict_opts, session=session)

        except (KeyError, ValueError) as exc:
            raise HTTPException(detail=repr(exc), status_code=400) from exc
        
        api_logger.debug(f"asf.ASFSearchOptions object constructed: {opts})")
        return opts
    
    def _get_search_options_dict(self) -> dict:
        return self.model_dump(exclude_none=True, exclude_unset=True, exclude=self.excluded_fields)
    
class BaselineParamsModel(ParamsModel):
    reference: str

    excluded_fields = ['reference', *ParamsModel.excluded_fields]