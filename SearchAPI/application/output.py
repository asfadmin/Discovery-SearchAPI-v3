import asf_search as asf
from asf_search import ASFSearchResults, ASFSearchOptions, granule_search
from typing import Generator
from fastapi.responses import StreamingResponse
from datetime import datetime
from . import constants

def as_output(search_generator: Generator[ASFSearchResults, None, None], output: str):
    output_format = output.lower()

    output_config = {
        'jsonlite': {
            'content': yield_jsonlite(search_generator),
            'media_type': 'application/json; charset=utf-8',
            'headers': {
                **constants.DEFAULT_HEADERS,
                'Content-Disposition': f"attachment; filename={make_filename('json')}",
            }
        },
        'jsonlite2': {
            'content': yield_jsonlite2(search_generator),
            'media_type': 'application/json; charset=utf-8',
            'headers': {
                **constants.DEFAULT_HEADERS,
                'Content-Disposition': f"attachment; filename={make_filename('json')}",
            }
        },
        'geojson': {
            'content': yield_geojson(search_generator),
            'media_type': 'application/geojson; charset=utf-8',
            'headers': {
                **constants.DEFAULT_HEADERS,
                'Content-Disposition': f"attachment; filename={make_filename('geojson')}",
            }
        },
        'csv': {
            'content': yield_csv(search_generator),
            'media_type': 'text/csv; charset=utf-8',
            'headers': {
                **constants.DEFAULT_HEADERS,
                'Content-Disposition': f"attachment; filename={make_filename('csv')}",
            }
        },
        'kml': {
            'content': yield_kml(search_generator),
            'media_type': 'application/vnd.google-earth.kml+xml; charset=utf-8',
            'headers': {
                **constants.DEFAULT_HEADERS,
                'Content-Disposition': f"attachment; filename={make_filename('kml')}",
            }
        },
        'metalink': {
            'content': yield_metalink(search_generator),
            'media_type': 'application/metalink+xml; charset=utf-8',
            'headers': {
                **constants.DEFAULT_HEADERS,
                'Content-Disposition': f"attachment; filename={make_filename('metalink')}",
            }
        }
    }
    if output_format not in output_config:
        raise ValueError(f"Unknown output '{output_format}' was requested.")
    return output_config[output_format]

def get_baseline(reference: str, opts: ASFSearchOptions):
    ref = granule_search(granule_list=[reference])

    return StreamingResponse(
            yield_jsonlite2(ref[0].stack(opts=opts)),
            media_type='application/json; charset=utf-8',
             headers={
                 **constants.DEFAULT_HEADERS,
                 'Content-Disposition': f"attachment; filename={make_filename('json')}",
             }
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

def make_filename(suffix):
    return f'asf-datapool-results-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.{suffix}'
