from typing import Literal
import requests
import json
import asf_search as asf

from fastapi import HTTPException

from datetime import datetime

from . import constants
from . import asf_env

asf_search_script_template = '''## This script requires that the asf-search python module is installed
## to install, run the following in a terminal
## `pip install asf-search`
## Then from the correct folder in your terminal run:
## `python {0}`
## 
## For more information, see the official documentation
## https://docs.asf.alaska.edu/asf_search/basics/
import asf_search as asf
import pprint

opts=asf.ASFSearchOptions(**{1})

## if the search requires authentication, uncomment
## the lines below, and enter your EDL credentials when prompted
## (use `session.auth_with_token(getpass('EDL Token'))` instead if a CMR bearer token is required)
# from get_pass import get_pass
# session=asf.ASFSession()
# session.auth_with_creds(input('EDL Username'), getpass('EDL Password'))
# opts.session = session

results=asf.search(opts=opts)
pprint.pp(results.geojson())

'''

asf_search_baseline_script_template= '''## This script requires that the asf-search python module is installed
## to install, run the following in a terminal
## `pip install asf-search`
## Then from the correct folder in your terminal run:
## `python {0}`

## For more information, see the official documentation
## https://docs.asf.alaska.edu/asf_search/basics/
import asf_search as asf
import pprint

opts=asf.ASFSearchOptions(**{2})

## if the search requires authentication, uncomment
## the lines below, and enter your EDL credentials when prompted
## (use `session.auth_with_token(getpass('EDL Token'))` instead if a CMR bearer token is required)
# from get_pass import get_pass
# session=asf.ASFSession()
# session.auth_with_creds(input('EDL Username'), getpass('EDL Password'))
# opts.session = session

reference_product = asf.granule_search(granule_list=['{1}'], opts=opts)[0]
stack = reference_product.stack(opts=opts)

pprint.pp(stack.geojson())

'''

def as_output(results: asf.ASFSearchResults, output: str) -> dict:
    output_format = output.lower()

    # Use a switch statement, so you only load the type of output you need:
    match output_format:
        case 'json':
            return {
                'content': ''.join(results.json()),
                'media_type': 'application/json; charset=utf-8',
                'headers': {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={make_filename('json')}",
                }
            }
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
    # Load basic consts:
    script_url = asf_env.load_config_maturity()['bulk_download_api']
    file_type = asf.FileDownloadType.DEFAULT_FILE
    # Build the url list:
    url_list = []
    for product in results:
        url_list.extend(product.get_urls(fileType=file_type))

    # Setup the data you're posting with. Optional filename so it lines up with our headers:
    script_data = {'products': ','.join(url_list)}
    if filename:
        script_data['filename'] = filename
    # Finally make the request:
    script_request = requests.post(script_url, data=script_data, timeout=30)
    return script_request.text

def get_asf_search_script(
        opts: asf.ASFSearchOptions,
        reference: str = None,
        search_endpoint: Literal['param', 'baseline'] = 'param'
        ) -> tuple[str, str]:
    
    opts.session = None
    # ASFSearchOptions formatting uses json.dumps for serialization. Add proper python capitalization
    opts_str = str(opts).replace('true', 'True', -1).replace('false', 'False')
    if search_endpoint == 'param':
        file_name=make_filename('py', prefix='asf-search-script')
        output_script = asf_search_script_template.format(file_name, opts_str)
    else:
        file_name=make_filename('py', prefix='asf-search-baseline-script')
        output_script = asf_search_baseline_script_template.format(file_name, reference, opts_str)
    return file_name, output_script

def make_filename(suffix, prefix:str = 'asf-results'):
    return f'{prefix}-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.{suffix}'
