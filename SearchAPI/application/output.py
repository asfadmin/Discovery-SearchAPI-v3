import requests
import json
import asf_search as asf
from asf_search import ASFSearchResults, ASFSearchOptions, granule_search
from typing import Generator
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from datetime import datetime
from . import constants
from . import asf_env

from SearchAPI import api_logger
from tenacity import retry, stop_after_attempt

def as_output(results: asf.ASFSearchResults, output: str) -> dict:
    output_format = output.lower()
    if output_format == "json":
        output_format = "jsonlite"

    # Use a switch statement, so you only load the type of output you need:
    match output_format:
        case 'jsonlite':
            return {
                'content': ''.join(results.jsonlite()),
                'media_type': 'application/json; charset=utf-8',
                'headers': {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={make_filename('json')}",
                }
            }
        case 'jsonlite2':
            return {
                'content': ''.join(results.jsonlite2()),
                'media_type': 'application/json; charset=utf-8',
                'headers': {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={make_filename('json')}",
                }
            }
        case 'geojson':
            return {
                'content': json.dumps(results.geojson(), indent=4),
                'media_type': 'application/geo+json; charset=utf-8',
                'headers': {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={make_filename('geojson')}",
                }
            }
        case 'csv':
            return {
                'content': ''.join(results.csv()),
                'media_type': 'text/csv; charset=utf-8',
                'headers': {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={make_filename('csv')}",
                }
            }
        case 'kml':
            return {
                'content': ''.join(results.kml()),
                'media_type': 'application/vnd.google-earth.kml+xml; charset=utf-8',
                'headers': {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={make_filename('kml')}",
                }
            }
        case 'metalink':
            return {
                'content': ''.join(results.metalink()),
                'media_type': 'application/metalink+xml; charset=utf-8',
                'headers': {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={make_filename('metalink')}",
                }
            }
        case 'download':
            # Only call this once to guarantee the names always are the same:
            filename = make_filename('py')
            return {
                'content': get_download(results, filename=filename),
                'media_type': 'text/x-python',
                'headers': {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={filename}",
                }
            }
        # The default case. Throw if you get this far:
        case _:
            raise HTTPException(
                detail=f"Unknown output '{output_format}' was requested.",
                status_code=400
            )

def get_download(results: asf.ASFSearchResults, filename=None):
    if len(results) == 0:
        return
    # Load basic consts:
    script_url = asf_env.load_config_maturity()['bulk_download_api']
    file_type = asf.FileDownloadType.DEFAULT_FILE
    
    # Build the url list:
    url_list = []
    for product in results:
        url_list.extend(product.get_urls(fileType=file_type))

    product_urls_str = ','.join(url_list)

    return _bulk_download_query(url=script_url, product_urls_str=product_urls_str, filename=filename )
    

@retry(stop=stop_after_attempt(3),reraise=True)
def _bulk_download_query(url: str, product_urls_str: str, filename: str = None):
    data = { 'products': product_urls_str }

    # Optional filename so it lines up with our headers:
    if filename is not None:
        data['filename'] = filename

    script_request = requests.post(url=url, data=data, timeout=30 )
    script_request.raise_for_status()

    return script_request.text

def make_filename(suffix):
    return f'asf-results-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.{suffix}'
