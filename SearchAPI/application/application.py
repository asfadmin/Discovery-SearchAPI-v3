
import json
import logging
import os
import dateparser
from pydantic import BaseModel

import asf_search as asf
from fastapi import Depends, FastAPI, Request, HTTPException, APIRouter, UploadFile
from fastapi.responses import Response, JSONResponse, StreamingResponse

from SearchAPI import api_logger, log_router

from WKTUtils import FilesToWKT
from .asf_env import load_config_maturity
from .asf_opts import WKTModel, get_asf_opts
from .health import get_cmr_health
from .output import as_output
from . import constants
from shapely import from_wkt

asf.REPORT_ERRORS = False
router = APIRouter(route_class=log_router.LoggingRoute)
app = FastAPI()


@router.api_route("/services/search/param", methods=["GET", "POST", "HEAD"])
async def query_params(output: str='metalink', opts: asf.ASFSearchOptions = Depends(get_asf_opts)):
    # TODO: Now that we don't have to use streaming responses, this count
    #       block could probably be moved to 'as_output', especially
    #       since it's a switch statement now.
    if output.lower() == 'count':
        return Response(
            content=str(asf.search_count(opts=opts)),
            status_code=200,
            media_type='text/html; charset=utf-8',
            headers=constants.DEFAULT_HEADERS
        )
    else:
        try:
            results = asf.search(opts=opts)
            response_info = as_output(results, output)
            return Response(**response_info)

        except (asf.ASFSearchError, asf.CMRError, ValueError) as exc:
            raise HTTPException(detail=f"Search failed to find results: {exc}", status_code=400) from exc


@router.api_route("/services/search/baseline", methods=["GET", "POST", "HEAD"])
async def query_baseline(request: Request, reference: str, output: str='metalink', opts: asf.ASFSearchOptions = Depends(get_asf_opts)):
    opts.maxResults = None
    # Load the reference scene:
    try:
        reference_product = asf.granule_search(granule_list=[reference], opts=opts)[0]
    except (KeyError, IndexError, ValueError) as exc:
        raise HTTPException(detail=f"Reference scene not found: {reference}", status_code=400) from exc
    
    try:
        if reference_product.get_stack_opts() is None:
            reference_product = asf.ASFStackableProduct(args={'umm': reference_product.umm, 'meta': reference_product.meta}, session=reference_product.session)
        if not reference_product.has_baseline() or not reference_product.is_valid_reference():
            raise asf.exceptions.ASFBaselineError(f"Requested reference scene has no baseline")
    except (asf.exceptions.ASFBaselineError, ValueError) as exc:
        raise HTTPException(detail=f"Search failed to find results: {exc}", status_code=400)
    
    if request.method == "HEAD":
        # Need head request separately, so it doesn't do all
        # the work to figure out the body
        if output.lower() == 'count':
            return Response(
                status_code=200,
                media_type='text/html; charset=utf-8',
                headers=constants.DEFAULT_HEADERS
            )
        metadata = as_output(asf.ASFSearchResults([]), output)
        return Response(
            status_code=200,
            headers=metadata["headers"],
            media_type=metadata["media_type"]
        )
    # Figure out the response params:
    if output.lower() == 'count':
        stack_opts = reference_product.get_stack_opts()
        return Response(
            content=str(asf.search_count(opts=stack_opts)),
            status_code=200,
            media_type='text/html; charset=utf-8',
            headers=constants.DEFAULT_HEADERS
        )
    
    # Finally stream everything back:
    try:
        response_info = as_output(reference_product.stack(opts=opts), output)
        return Response(**response_info)

    except (asf.ASFSearchError, asf.CMRError, ValueError) as exc:
        raise HTTPException(detail=f"Search failed to find results: {exc}", status_code=400) from exc



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
    
@router.api_route("/services/utils/wkt", methods=["GET", "POST"])
async def query_wkt_validation(body: WKTModel, wkt: str=''): # = Depends()): #, wkt: str | None = None):
    if len(wkt) == 0:
       wkt = body.wkt
    # params = dict(request.query_params)
    # try:
    #     if params.get('wkt') is not None:
    #         wkt = params['wkt']
        # else:
        #     raise KeyError(f'Missing required key, "wkt" in request body')
    

    return Response(
        content=json.dumps(validate_wkt(wkt)),
        status_code=200,
        media_type = 'application/json; charset=utf-8',
        headers=constants.DEFAULT_HEADERS
    )

@router.post('/services/utils/files_to_wkt')
async def file_to_wkt(files: UploadFile):
    # file.content_type
    api_logger.debug(f"Uploaded file: {files.filename}\n{files.content_type}\n")
    files.file.filename = files.filename
    data = FilesToWKT.filesToWKT([files.file]).getWKT()
    api_logger.debug(f"{data}")
    return validate_wkt(data["parsed wkt"])

def validate_wkt(wkt: str):
    try:
        wrapped, unwrapped, reports = asf.validate_wkt(wkt)
        repairs = [{'type': report.report_type, 'report': report.report} for report in reports]
    except Exception as exc:
        raise HTTPException(detail=f"Failed to validate wkt: {exc}", status_code=400) from exc

    return {
        'wkt': {
            'unwrapped': unwrapped.wkt,
            'wrapped': wrapped.wkt
        },
        'repairs':  repairs
    }

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
