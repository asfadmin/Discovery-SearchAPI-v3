from collections import defaultdict

import dateparser
import asf_search as asf
from asf_search import ASFSearchResults, ASFProduct
from shapely.wkt import dumps as dump_to_wkt
from shapely import Polygon

from asf_enumeration import aria_s1_gunw

def stack_aria_gunw(frame_id: str):
    reference, aria_groups = get_aria_groups_for_frame(frame_id)
    
    stack = ASFSearchResults([group.products[0] for group in aria_groups])
    target_stack, warnings = asf.baseline.get_baseline_from_stack(reference, stack)

    return target_stack

def get_aria_groups_for_frame(frame: str) -> tuple[ASFProduct, list[aria_s1_gunw.Sentinel1Acquisition]]:
    aria_frame = aria_s1_gunw.get_frame(frame_id=int(frame))
    groups = aria_s1_gunw.get_acquisitions(aria_frame)
    return groups[0].products[0], groups
