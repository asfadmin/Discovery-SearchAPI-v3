import json
import logging
import os

import asf_search as asf
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import Response, StreamingResponse

from asf_env import get_config, load_config
from SearchAPIQuery import SearchAPIQuery
from health import get_cmr_health
from output import as_output, get_baseline, make_filename

asf.REPORT_ERRORS = False
app = FastAPI()

@app.post("/services/search/param")
@app.get("/services/search/param")
def query_params(opts: SearchAPIQuery = Depends(), output: str = 'jsonlite'):
    if output.lower() != 'count':
        return as_output(asf.search_generator(opts=opts), output)
    else:
        count = asf.search_count(opts=opts)
        logging.warn(f"FOUND {count} results")
        return Response(str(count), 200, media_type='text/plain; charset=utf-8', headers={'Access-Control-Expose-Headers': 'Content-Disposition', 'Access-Control-Allow-Origin': '*'})

@app.post("/services/search/baseline")
@app.get("/services/search/baseline")
def query_params(reference: str, opts: SearchAPIQuery = Depends()):
    opts.maxResults = None
    return get_baseline(reference, opts)
    
@app.get('/services/utils/mission_list')
def missionList(platform: str | None = None):
    if platform != None:
        platform = platform.upper()
    return Response(json.dumps({'result' :asf.campaigns(platform)}, sort_keys=True, indent=4), 200, media_type='application/json', headers={'Access-Control-Expose-Headers': 'Content-Disposition', 'Access-Control-Allow-Origin': '*'})
     

@app.get("/services/utils/wkt")
def query_params(wkt: str):
    wrapped, unwrapped, reports = asf.validate_wkt(wkt)

    res =         json.dumps({'wkt': {
            'unwrapped': unwrapped,
            'wrapped': wrapped
        },
    'repairs': [{'type': report.report_type, 'report': report.report} for report in reports] if len(reports) else []
    })
    logging.warn(res)
    return Response(res, 200, media_type='application/json', headers={'Access-Control-Expose-Headers': 'Content-Disposition', 'Access-Control-Allow-Origin': '*'})

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
    api_health = {'ASFSearchAPI': {'ok?': True, 'version': api_version['version'], 'config': get_config()}, 'CMRSearchAPI': cmr_health}
    # response = make_response(json.dumps(api_health, sort_keys=True, indent=2))
    return Response(content=json.dumps(api_health, sort_keys=True, indent=2), media_type='application/json; charset=utf-8', headers={'Access-Control-Allow-Origin': '*'})
    # response.mimetype = 'application/json; charset=utf-8'
    # return response
    
########## Helper functionality ##########

@app.exception_handler(HTTPException)
def handle_error(error: HTTPException):
    resp = Response(json.dumps({'errors': [{'type': 'VALUE', 'report': error.detail}] }, sort_keys=True, indent=2), status=413, mimetype='application/json', headers={'Access-Control-Allow-Origin': '*'})
    return resp
