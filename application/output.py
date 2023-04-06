import json
from time import perf_counter
import asf_search as asf
from asf_search import ASFSearchResults, ASFSearchOptions, granule_search
from typing import Generator
from fastapi.responses import StreamingResponse, Response
import logging
from datetime import datetime




def as_output(search_generator: Generator[ASFSearchResults, None, None], output: str):
    output = output.lower()
    if output == 'jsonlite':
        return StreamingResponse(yield_jsonlite(search_generator), media_type='application/json; charset=utf-8', headers={'Content-Disposition': f"attachment; filename={make_filename('json')}", 'Access-Control-Expose-Headers': 'Content-Disposition', 'Access-Control-Allow-Origin': '*'})
    elif output == 'jsonlite2':
        return StreamingResponse(yield_jsonlite2(search_generator), media_type='application/json; charset=utf-8', headers={'Content-Disposition': f"attachment; filename={make_filename('json')}", 'Access-Control-Expose-Headers': 'Content-Disposition', 'Access-Control-Allow-Origin': '*'})
    elif output == 'geojson':
        return StreamingResponse(yield_geojson(search_generator), media_type='application/geojson; charset=utf-8', headers={'Content-Disposition': f"attachment; filename={make_filename('geojson')}", 'Access-Control-Expose-Headers': 'Content-Disposition', 'Access-Control-Allow-Origin': '*'})
    elif output == 'csv':
        return StreamingResponse(yield_csv(search_generator), media_type='text/csv; charset=utf-8', headers={'Content-Disposition': f"attachment; filename={make_filename('csv')}", 'Access-Control-Expose-Headers': 'Content-Disposition', 'Access-Control-Allow-Origin': '*'})
    elif output == 'kml':
        return StreamingResponse(yield_kml(search_generator), media_type='application/vnd.google-earth.kml+xml; charset=utf-8', headers={'Content-Disposition': f"attachment; filename={make_filename('kml')}", 'Access-Control-Expose-Headers': 'Content-Disposition', 'Access-Control-Allow-Origin': '*'})
    elif output == 'metalink':
        return StreamingResponse(yield_metalink(search_generator), media_type='application/metalink+xml; charset=utf-8', headers={'Content-Disposition': f"attachment; filename={make_filename('metalink')}", 'Access-Control-Expose-Headers': 'Content-Disposition', 'Access-Control-Allow-Origin': '*'})

def get_baseline(reference: str, opts: ASFSearchOptions):
    ref = granule_search(granule_list=[reference])
    return StreamingResponse(yield_jsonlite2(iter([ref[0].stack(opts=opts)])), media_type='application/json; charset=utf-8', 
                             headers={'Content-Disposition': f"attachment; filename={make_filename('json')}", 'Access-Control-Expose-Headers': 'Content-Disposition', 'Access-Control-Allow-Origin': '*'})

def yield_jsonlite(result_gen: Generator[ASFSearchResults, None, None]):
    for page in asf.export.jsonlite.results_to_jsonlite(result_gen):
        yield page
        
def yield_jsonlite2(result_gen: Generator[ASFSearchResults, None, None]):
    for page in asf.export.jsonlite2.results_to_jsonlite2(result_gen):
        yield page
        

def yield_geojson(result_gen: Generator[ASFSearchResults, None, None]):
    for page in asf.export.results_to_geojson(result_gen):
        yield page
        # yield from asf.export.export_translators.output_translators()['geojson'](page)

def yield_csv(result_gen: Generator[ASFSearchResults, None, None]):
    csv_stream = asf.export.results_to_csv(result_gen)
    for page in csv_stream:
        yield from page
    # for page in result_gen:
    #     # asf.export.export_translators.results_to_format(asf.export.csv.get_additional_csv_fields, asf.export.csv.get_csv)(page)
    #     yield from asf.export.export_translators.output_translators()['csv'](page)

def yield_kml(result_gen: Generator[ASFSearchResults, None, None]):
    # for page in result_gen:
    #     yield from asf.export.export_translators.output_translators()['kml'](page)
    # kml_stream = asf.export.results_to_kml(result_gen)
    for page in asf.export.results_to_kml(result_gen):
        yield from page

def yield_metalink(result_gen: Generator[ASFSearchResults, None, None]):
    # metalink_stream = 
    for page in asf.export.results_to_metalink(result_gen):
        yield from page
    
def make_filename(suffix):
    return f'asf-datapool-results-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.{suffix}'