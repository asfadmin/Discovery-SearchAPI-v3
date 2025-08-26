from datetime import datetime
import io
import json

import os
from typing import Optional
import dateparser

import asf_search as asf
from fastapi import Depends, FastAPI, Request, HTTPException, APIRouter, UploadFile
from fastapi.responses import FileResponse, RedirectResponse, Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .log_router import LoggingRoute
from .logger import api_logger
from .asf_env import load_config_maturity
from .asf_opts import process_baseline_request, process_search_request, process_wkt_request
from .health import get_cmr_health
from .models import BaselineSearchOptsModel, SearchOptsModel
from .output import as_output, get_asf_search_script
from .files_to_wkt import FilesToWKT
from . import constants
from .SearchAPISession import SearchAPISession
from asf_search.ASFSearchOptions.config import config as asf_config
from .browse_reproject import nisar_browse_kml

asf_config['session'] = SearchAPISession()

asf.REPORT_ERRORS = False
router = APIRouter(route_class=LoggingRoute)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@router.api_route("/services/search/param", methods=["GET", "POST", "HEAD"])
async def query_params(searchOptions: SearchOptsModel = Depends(process_search_request)):
    # TODO: Now that we don't have to use streaming responses, this count
    #       block could probably be moved to 'as_output', especially
    #       since it's a switch statement now.
    output = searchOptions.output
    opts = searchOptions.opts

    non_search_param = ['output', 'maxresults', 'pagesize', 'maturity']
    try:
        any_searchables = any([key.lower() not in non_search_param for key, _ in opts])
        if not any_searchables:
            raise ValueError(
                'No searchable parameters specified, queries must include'
                ' parameters besides output= and maxresults='
            )
    except ValueError as exc:
        raise HTTPException(detail=repr(exc), status_code=400) from exc

    if output.lower() == 'count':
        count=asf.search_count(opts=opts)
        return Response(
            content=str(count),
            status_code=200,
            media_type='text/html; charset=utf-8',
            headers=constants.DEFAULT_HEADERS
        )

    if output.lower() == 'python':
        file_name, search_script = get_asf_search_script(opts)
        
        return Response(
            content=search_script,
            status_code=200,
            media_type='text/x-python',
            headers= {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={file_name}",
                }
        )
    try:
        results = asf.search(opts=opts)
        response_info = as_output(results, output)
        return Response(**response_info)

    except (asf.ASFSearchError, asf.CMRError, ValueError) as exc:
        raise HTTPException(
            detail=f"Search failed to find results: {exc}",
            status_code=400
        ) from exc


@router.api_route("/services/search/baseline", methods=["GET", "POST", "HEAD"])
async def query_baseline(searchOptions: BaselineSearchOptsModel = Depends(process_baseline_request)):
    opts = searchOptions.opts
    opts.maxResults = None
    output = searchOptions.output
    reference = searchOptions.reference
    request_method = searchOptions.request_method

    is_frame_based = searchOptions.opts.dataset is not None

    # Load the reference scene:
    
    if output.lower() == 'python':
        file_name, search_script = get_asf_search_script(opts, reference=reference, search_endpoint='baseline')
        
        return Response(
            content=search_script,
            status_code=200,
            media_type='text/x-python',
            headers= {
                    **constants.DEFAULT_HEADERS,
                    'Content-Disposition': f"attachment; filename={file_name}",
                }
        )

    # reference_product = None
    if is_frame_based and opts.dataset[0] == asf.DATASET.ARIA_S1_GUNW:
        try:
            reference_product = asf.search(frame=int(reference), opts=opts, maxResults=1)[0]
        except (KeyError, IndexError, ValueError) as exc:
            raise HTTPException(detail=f"Reference scene not found with frame: {reference}", status_code=400) from exc

    else:
        try:
            reference_product = asf.granule_search(granule_list=[reference], opts=opts)[0]
        except (KeyError, IndexError, ValueError) as exc:
            raise HTTPException(detail=f"Reference scene not found: {reference}", status_code=400) from exc

    try:
        if reference_product.get_stack_opts() is None:
            reference_product = asf.ASFStackableProduct(args={'umm': reference_product.umm, 'meta': reference_product.meta}, session=reference_product.session)
        if (not reference_product.has_baseline() or not reference_product.is_valid_reference() or not reference_product.has_baseline()) and not is_frame_based:
            raise asf.exceptions.ASFBaselineError(f"Requested reference scene has no baseline")
    except (asf.exceptions.ASFBaselineError, ValueError) as exc:
        raise HTTPException(detail=f"Search failed to find results: {exc}", status_code=400)

    if request_method == "HEAD":
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
        count = asf.search_count(opts=stack_opts)

        return Response(
            content=str(count),
            status_code=200,
            media_type='text/html; charset=utf-8',
            headers=constants.DEFAULT_HEADERS
        )

    # Finally stream everything back:
    try:
        stack = reference_product.stack(opts=opts)
        response_info = as_output(stack, output)
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

    response = {'result': asf.campaigns(platform)}

    return JSONResponse(
        content=response,
        status_code=200,
        headers=constants.DEFAULT_HEADERS
    )


@router.api_route("/services/utils/wkt", methods=["GET", "POST"])
async def wkt_validation(wkt: str = Depends(process_wkt_request)):
    return Response(
        content=json.dumps(validate_wkt(wkt)),
        status_code=200,
        media_type='application/json; charset=utf-8',
        headers=constants.DEFAULT_HEADERS
    )

@router.post('/services/utils/files_to_wkt')
async def file_to_wkt(files: list[UploadFile]):
    for file in files:
        file.file.filename = file.filename

    data = FilesToWKT([file.file for file in files]).getWKT()

    return JSONResponse(content={
        ** data,
        ** validate_wkt(data["parsed wkt"])},
        status_code=200,
        headers=constants.DEFAULT_HEADERS
    )

# @router.get('/redirect/{shortName}')
# async def nisar_static_layer(shortName: str, granule_id: str, cmr_token: Optional[str], cmr_host: Optional[str]='uat'):
#         opts = asf.ASFSearchOptions()
#         if cmr_token is not None:
#             if cmr_host == 'uat':
#                 host = asf.INTERNAL.CMR_HOST_UAT
#             else:
#                 host = asf.INTERNAL.CMR_HOST
#             session = asf.ASFSession(cmr_host=host).auth_with_token(cmr_token)
#             opts.session = session
#             opts.host = host
#         try:
#             granule = asf.search(
#                 granule_list=[granule_id],
#                 opts=opts
#                 )[0]
#         except IndexError:
#             raise HTTPException(status_code=400, detail=f'Unable to find static layer, provided scene named "{granule_id}" not found in CMR record')
        
#         static_layer = granule.get_static_layer(opts=asf.ASFSearchOptions(shortName=shortName))
#         if static_layer is None:
#             raise HTTPException(status_code=500, detail=f'Static layer not found for scene named "{granule_id}"')

#         return RedirectResponse(static_layer.properties['url'])

@router.get('/services/utils/nisar_browse_reproject')
def nisar_browse_reproject(product_ur: str, cmr_token: str):
    session = asf.ASFSession(cmr_host=asf.INTERNAL.CMR_HOST_UAT).auth_with_token(cmr_token)
    opts = asf.ASFSearchOptions(host=asf.INTERNAL.CMR_HOST_UAT, session=session)

    response = asf.search(product_list=[product_ur], opts=opts)[0]

    
    kml_url = response.find_urls('.kml')[0]
    kml_data  = session.get(kml_url).text
    png_url = response.find_urls('.png')[0]
    fl = response.properties['flightDirection'].lower()

    res = session.get(png_url, stream=True)
    png_file = io.BytesIO(res.content)
    # return JSONResponse(nisar_browse_kml(kml_data), headers=constants.DEFAULT_HEADERS)
    nisar_browse_kml(kml_data, png_file, 'output.png', orbit_direction=fl)
    
    return FileResponse('./2output.png', status_code=200, headers=constants.DEFAULT_HEADERS, media_type='image/png')
    # return Response(headers=constants.DEFAULT_HEADERS)
    pass

def validate_wkt(wkt: str):
    try:
        wrapped, unwrapped, reports = asf.validate_wkt(wkt)
        repairs = [{'type': report.report_type, 'report': report.report} for report in reports if report.report_type != "'type': 'WRAP'"]
    except Exception as exc:
        raise HTTPException(detail=f"Failed to validate wkt {wkt}: {exc}", status_code=400) from exc

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
        api_logger.info(exc)
        api_version = {'version': 'unknown'}

    cfg = load_config_maturity()
    cmr_health = get_cmr_health(cfg['cmr_base'], cfg['cmr_health'])

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
