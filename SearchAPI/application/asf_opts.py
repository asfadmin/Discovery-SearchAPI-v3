
from fastapi import HTTPException, Request
import asf_search as asf

def get_asf_opts(request: Request) -> asf.ASFSearchOptions:
    params = dict(request.query_params)
    # SearchOpts doesn't know how to handle these keys, but other methods need them
    # (We still want to throw on any UNKNOWN keys)
    ignore_keys = ["output", "reference"]
    params = {k: params[k] for k in params.keys() if k not in ignore_keys}

    try:
        return asf.ASFSearchOptions(**params)
    except (KeyError, ValueError) as exc:
        raise HTTPException(detail=repr(exc), status_code=400) from exc