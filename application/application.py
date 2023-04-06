import json
import logging
import os

import asf_search as asf
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import Response, StreamingResponse

from .asf_env import get_config, load_config
from .SearchAPIQuery import SearchAPIQuery
from .health import get_cmr_health
from .output import as_output, get_baseline, make_filename
from . import constants

asf.REPORT_ERRORS = False
app = FastAPI()

@app.post("/services/search/param")
@app.get("/services/search/param")
def query_params(opts: SearchAPIQuery = Depends(), output: str = 'jsonlite'):
    if output.lower() != 'count':
        return as_output(asf.search_generator(opts=opts), output)
    else:
        response = str(asf.search_count(opts=opts))

        return Response(
            content=response,
            status_code=200,
            media_type='text/plain; charset=utf-8',
            headers=constants.DEFAULT_HEADERS
        )

@app.post("/services/search/baseline")
@app.get("/services/search/baseline")
def query_params(reference: str, opts: SearchAPIQuery = Depends()):
    opts.maxResults = None
    return get_baseline(reference, opts)

@app.get('/services/utils/mission_list')
def missionList(platform: str | None = None):
    if platform != None:
        platform = platform.upper()

    response = json.dumps({'result' :asf.campaigns(platform)}, sort_keys=True, indent=4)

    return Response(
        content=response,
        status_code=200,
        media_type='application/json',
        headers=constants.DEFAULT_HEADERS
    )


@app.get("/services/utils/wkt")
def query_params(wkt: str):
    wrapped, unwrapped, reports = asf.validate_wkt(wkt)

    repairs = [{'type': report.report_type, 'report': report.report} for report in reports]
    response = json.dumps({
        'wkt': {
            'unwrapped': unwrapped,
            'wrapped': wrapped
        },
        'repairs':  repairs
    })

    return Response(
        content=response,
        status_code=200,
        media_type='application/json',
        headers=constants.DEFAULT_HEADERS
    )

@app.get('/')
@app.get('/health')
def health_check():
    try:
        version_path = os.path.join("SearchAPI", "version.json")
        with open(version_path, 'r', encoding="utf-8") as version_file:
            api_version = json.load(version_file)
    except Exception as e:
        logging.debug(e)
        api_version = {'version': 'unknown'}

    cmr_health = get_cmr_health()
    api_health = {
        'ASFSearchAPI': {
            'ok?': True,
            'version': api_version['version'],
            'config': get_config()
        },
        'CMRSearchAPI': cmr_health
    }

    response = json.dumps(api_health, sort_keys=True, indent=4)

    return Response(
        content=response,
        status_code=200,
        media_type='application/json; charset=utf-8',
        headers=constants.DEFAULT_HEADERS
    )

@app.exception_handler(HTTPException)
def handle_error(error: HTTPException):
    response = json.dumps({'errors': [{'type': 'VALUE', 'report': error.detail}] }, sort_keys=True, indent=4)

    return Response(
        content=response,
        status=400,
        mimetype='application/json',
        headers=constants.DEFAULT_HEADERS
    )
