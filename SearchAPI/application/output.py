import requests

import asf_search as asf
from asf_search import ASFSearchResults, ASFSearchOptions, granule_search
from typing import Generator
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from datetime import datetime
from . import constants
from . import asf_env

def as_output(search_generator: Generator[ASFSearchResults, None, None], output: str) -> dict:
    output_format = output.lower()

    # Use a switch statement, so you only load the type of output you need:
    match output_format:
        case 'jsonlite':
            return {
                'content': yield_jsonlite(search_generator),
                'media_type': 'application/json; charset=utf-8',
                'headers': {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={make_filename('json')}",
                }
            }
        case 'jsonlite2':
            return {
                'content': yield_jsonlite2(search_generator),
                'media_type': 'application/json; charset=utf-8',
                'headers': {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={make_filename('json')}",
                }
            }
        case 'geojson':
            return {
                'content': yield_geojson(search_generator),
                'media_type': 'application/geojson; charset=utf-8',
                'headers': {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={make_filename('geojson')}",
                }
            }
        case 'csv':
            return {
                'content': yield_csv(search_generator),
                'media_type': 'text/csv; charset=utf-8',
                'headers': {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={make_filename('csv')}",
                }
            }
        case 'kml':
            return {
                'content': yield_kml(search_generator),
                'media_type': 'application/vnd.google-earth.kml+xml; charset=utf-8',
                'headers': {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={make_filename('kml')}",
                }
            }
        case 'metalink':
            return {
                'content': yield_metalink(search_generator),
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
                'content': yield_download(search_generator, filename=filename),
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



def yield_jsonlite(result_gen: Generator[ASFSearchResults, None, None]):
    for page in asf.export.jsonlite.results_to_jsonlite(result_gen):
        yield page

def yield_jsonlite2(result_gen: Generator[ASFSearchResults, None, None]):
    for page in asf.export.jsonlite2.results_to_jsonlite2(result_gen):
        yield page

def yield_geojson(result_gen: Generator[ASFSearchResults, None, None]):
    for page in asf.export.results_to_geojson(result_gen):
        yield page

def yield_csv(result_gen: Generator[ASFSearchResults, None, None]):
    csv_stream = asf.export.results_to_csv(result_gen)
    for page in csv_stream:
        yield page

def yield_kml(result_gen: Generator[ASFSearchResults, None, None]):
    for page in asf.export.results_to_kml(result_gen):
        yield page

def yield_metalink(result_gen: Generator[ASFSearchResults, None, None]):
    for page in asf.export.results_to_metalink(result_gen):
        yield page

def yield_download(result_gen: Generator[ASFSearchResults, None, None], filename=None):
    script_url = asf_env.load_config_maturity()['bulk_download_api']
    product_list = []
    for page in result_gen:
        product_list.extend([product.properties['url'] for product in page])
    # Setup the data you're posting with. Optional filename so it lines up with our headers:
    script_data = { 'products': ','.join(product_list) }
    if filename:
        script_data['filename'] = filename
    # Finally make the request:
    script_request = requests.post( script_url, data=script_data, timeout=30 )
    yield script_request.text

def make_filename(suffix):
    return f'asf-results-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.{suffix}'
