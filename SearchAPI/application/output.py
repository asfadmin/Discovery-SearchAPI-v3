import requests

import asf_search as asf
from asf_search import ASFSearchResults, ASFSearchOptions, granule_search
from typing import Generator
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from datetime import datetime
from . import constants
from . import asf_env

def as_output(results: asf.ASFSearchResults, output: str) -> dict:
    output_format = output.lower()
    if output_format == "json":
        output_format = "jsonlite"

    # Use a switch statement, so you only load the type of output you need:
    match output_format:
        case 'jsonlite':
            return {
                'content': get_jsonlite(results),
                'media_type': 'application/json; charset=utf-8',
                'headers': {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={make_filename('json')}",
                }
            }
        case 'jsonlite2':
            return {
                'content': get_jsonlite2(results),
                'media_type': 'application/json; charset=utf-8',
                'headers': {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={make_filename('json')}",
                }
            }
        case 'geojson':
            return {
                'content': get_geojson(results),
                'media_type': 'application/geojson; charset=utf-8',
                'headers': {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={make_filename('geojson')}",
                }
            }
        case 'csv':
            return {
                'content': get_csv(results),
                'media_type': 'text/csv; charset=utf-8',
                'headers': {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={make_filename('csv')}",
                }
            }
        case 'kml':
            return {
                'content': get_kml(results),
                'media_type': 'application/vnd.google-earth.kml+xml; charset=utf-8',
                'headers': {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={make_filename('kml')}",
                }
            }
        case 'metalink':
            return {
                'content': get_metalink(results),
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

def get_jsonlite(results: asf.ASFSearchResults):
    pages = [i for i in asf.export.results_to_jsonlite(results)]
    return ''.join(pages)

def get_jsonlite2(results: asf.ASFSearchResults):
    pages = [i for i in asf.export.jsonlite2.results_to_jsonlite2(results)]
    return ''.join(pages)

def get_geojson(results: asf.ASFSearchResults):
    pages = [i for i in asf.export.results_to_geojson(results)]
    return ''.join(pages)

def get_csv(results: asf.ASFSearchResults):
    pages = [i for i in asf.export.results_to_csv(results)]
    return ''.join(pages)

def get_kml(results: asf.ASFSearchResults):
    pages = [i for i in asf.export.results_to_kml(results)]
    return ''.join(pages)

def get_metalink(results: asf.ASFSearchResults):
    pages = [i for i in asf.export.results_to_metalink(results)]
    return ''.join(pages)

def get_download(results: asf.ASFSearchResults, filename=None):
    # Load basic consts:
    script_url = asf_env.load_config_maturity()['bulk_download_api']
    file_type = asf.FileDownloadType.DEFAULT_FILE
    # Build the url list:
    url_list = [url for result in results for url in result.get_urls(fileType=file_type)]
    # Setup the data you're posting with. Optional filename so it lines up with our headers:
    script_data = { 'products': ','.join(url_list) }
    if filename:
        script_data['filename'] = filename
    # Finally make the request:
    script_request = requests.post( script_url, data=script_data, timeout=30 )
    return script_request.text

def make_filename(suffix):
    return f'asf-results-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.{suffix}'
