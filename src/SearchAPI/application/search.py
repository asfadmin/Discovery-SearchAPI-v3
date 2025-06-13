from collections import defaultdict

import dateparser
import asf_search as asf
from shapely.wkt import dumps as dump_to_wkt
from shapely import Polygon

def stack_aria_gunw(frame: str):
    reference = asf.search(frame=int(frame), dataset=asf.DATASET.ARIA_S1_GUNW, maxResults=1)[0]

    opts = asf.ASFSearchOptions(
        relativeOrbit=reference.properties['pathNumber'],
        processingLevel=asf.PRODUCT_TYPE.SLC, 
        dataset=asf.DATASET.SENTINEL1, 
        beamMode='IW', 
        polarization=['VV','VV+VH'], 
        flightDirection=reference.properties['flightDirection'],
        intersectsWith=dump_to_wkt(Polygon(reference.geometry['coordinates'][0]))
    )

    slc_stack = asf.search(opts=opts)

    groups = defaultdict(list)
    for product in slc_stack:
        group_id = product.properties['platform'] + '_' + str(product.properties['orbit'])
        groups[group_id].append(product)
    # dateparser.parse(str(value))
    aria_groups = [
        {
            'date': min(dateparser.parse(product.properties['startTime']) for product in group),
            'products': [product for product in group],
        }
        for group in groups.values()
    ]

    # track group index on each product, naively choose first granule available
    for idx, group in enumerate(aria_groups):
        group_granule_idx = None
        for idy, product in enumerate(group['products']):
            product.properties['groupIDX'] = idx
            if group_granule_idx is None:
                if product.has_baseline():
                    group_granule_idx = idy
        
        group['group_granule_idx'] = group_granule_idx



    stack = asf.ASFSearchResults([group['products'][group['group_granule_idx']] for group in aria_groups if group['group_granule_idx'] is not None])
    target_stack, warnings = asf.baseline.get_baseline_from_stack(reference, stack)
    for product in target_stack:
        group_idx = product.properties.pop('groupIDX')
        aria_groups[group_idx]['perpendicularBaseline'] = product.properties['perpendicularBaseline']
        aria_groups[group_idx]['temporalBaseline'] = product.properties['temporalBaseline']
    
    for group in aria_groups:
        for idx, product in enumerate(group['products']):
            group['products'][idx] = product.properties['sceneName']
        group['date'] = group['date'].strftime('%Y-%m-%dT%H:%M:%SZ')
    
    return aria_groups