
import json
import logging
import os
import dateparser

import asf_search as asf
from fastapi import Depends, FastAPI, Request, HTTPException, APIRouter
from fastapi.responses import Response, JSONResponse, StreamingResponse

from SearchAPI import api_logger, log_router

from .asf_env import load_config_maturity
from .asf_opts import get_asf_opts
from .health import get_cmr_health
from .output import as_output
from . import constants

asf.REPORT_ERRORS = False
router = APIRouter(route_class=log_router.LoggingRoute)
app = FastAPI()


@router.post("/services/search/param")
@router.get("/services/search/param")
@router.head("/services/search/param")
async def query_params(output: str='jsonlite', opts: asf.ASFSearchOptions = Depends(get_asf_opts)):
    if output.lower() == 'count':
        return Response(
            content=str(asf.search_count(opts=opts)),
            status_code=200,
            media_type='text/plain; charset=utf-8',
            headers=constants.DEFAULT_HEADERS
        )
    else:
        response_info = as_output(asf.search_generator(opts=opts), output)
        return StreamingResponse(**response_info)


@router.post("/services/search/baseline")
@router.get("/services/search/baseline")
@router.head("/services/search/baseline")
async def query_baseline(request: Request, reference: str, output: str='jsonlite', opts: asf.ASFSearchOptions = Depends(get_asf_opts)):
    if request.method == "HEAD":
        # Need head request separately, so it doesn't do all
        # the work to figure out the body
        metadata = as_output(None, output)
        return Response(
            status_code=200,
            headers=metadata["headers"],
            media_type=metadata["media_type"]
        )
    opts.maxResults = None
    # Load the reference scene:
    try:
        ref = asf.granule_search(granule_list=[reference], opts=opts)[0]
    except KeyError as exc:
        raise HTTPException(detail=f"Reference scene not found: {reference}", status_code=400) from exc
    # Figure out the response params:
    response_info = as_output(ref.stack(opts=opts), output)
    # Finally stream everything back:
    return StreamingResponse(**response_info)


@router.get('/services/utils/date', response_class=JSONResponse)
async def query_date_validation(date: str):
    parsed_date = dateparser.parse(date)
    if parsed_date is None:
        raise HTTPException(detail=f"Could not parse date: {date}", status_code=400)

    response = {
        'date': {
            'original': date,
            'parsed': parsed_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    }
    return JSONResponse(
        content=response,
        status_code=200,
        headers=constants.DEFAULT_HEADERS
    )
@router.get('/services/utils/mission_list', response_class=JSONResponse)
async def query_mission_list(platform: str | None = None):
    if platform is not None:
        platform = platform.upper()

    response = { 'result': asf.campaigns(platform) }

    return JSONResponse(
        content=response,
        status_code=200,
        headers=constants.DEFAULT_HEADERS
    )


@router.get("/services/utils/wkt", response_class=JSONResponse)
async def query_wkt_validation(wkt: str):
    wrapped, unwrapped, reports = asf.validate_wkt(wkt)

    repairs = [{'type': report.report_type, 'report': report.report} for report in reports]
    response = {
        'wkt': {
            'unwrapped': unwrapped.wkt,
            'wrapped': wrapped.wkt
        },
        'repairs':  repairs
    }

    return JSONResponse(
        content=response,
        status_code=200,
        headers=constants.DEFAULT_HEADERS
    )

@router.get('/', response_class=JSONResponse)
@router.get('/health', response_class=JSONResponse)
async def health_check():
    try:
        version_path = os.path.join("SearchAPI", "version.json")
        with open(version_path, 'r', encoding="utf-8") as version_file:
            api_version = json.load(version_file)
    except Exception as exc:
        logging.debug(exc)
        api_version = {'version': 'unknown'}

    cmr_health = get_cmr_health()
    api_health = {
        'ASFSearchAPI': {
            'ok?': True,
            'version': api_version['version'],
            'config': load_config_maturity()
        },
        'CMRSearchAPI': cmr_health
    }

    return JSONResponse(
        content=api_health,
        status_code=200,
        headers=constants.DEFAULT_HEADERS
    )

@app.exception_handler(HTTPException)
async def handle_error(request: Request, error: HTTPException):
    response = {
        "error": {
            "type": "ERROR",
            "report": error.detail,
        }
    }
    return JSONResponse(
        content=response,
        status_code=error.status_code,
        headers=constants.DEFAULT_HEADERS
    )

app.include_router(router)
