
from pydantic import BaseModel, Field, InstanceOf, field_validator
from typing import ClassVar, Optional
from asf_search import ASFSearchOptions

class SearchOptsModel(BaseModel):
    """
    Unifies search request model
    opts (ASFSearchOptions): Generated from the params passed via query_params and the request body/json 
    request_method (str): The request method type
    output (str): the output type
    merged_args (dict): The merged query and body/json params (used for opts ASFSearchOptions doesn't keep track of like maturity, reference, etc)
    """
    opts: InstanceOf[ASFSearchOptions]
    request_method: str # ["GET", "POST", "HEAD"]
    output: Optional[str] = 'metalink'
    merged_args: dict = {}

    output_types: ClassVar[list[str]] = ['metalink', 'csv', 'geojson', 'json', 'jsonlite', 'jsonlite2', 'kml', 'count', 'download']

    @field_validator("output")
    def validate_output_format(cls, v):
        if v.lower() not in cls.output_types:
            raise ValueError(f'Output format {v} unsupported. Accepted output types: {cls.output_types}')
        
        return v
    
class BaselineSearchOptsModel(SearchOptsModel):
    """
    Baseline search request model
    """
    reference: str


class WKTModel(BaseModel):
    wkt: str = Field(default='')
