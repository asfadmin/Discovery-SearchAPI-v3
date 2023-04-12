import logging
from typing import List
import asf_search as asf
from datetime import datetime
from fastapi import Query

from .asf_env import load_maturity_config

class SearchAPIQuery(asf.ASFSearchOptions):
    def __init__(
        self,
        maxResults:             int | None = asf.INTERNAL.CMR_PAGE_SIZE,
        absoluteOrbit:          int | List[int] | None = None,
        asfFrame:               int | List[int] | None = None,
        asfPlatform:            str | None = Query(default=None, alias='asfplatform'),
        beamMode:               str | None = None,
        beamSwath:              str | None = None,
        campaign:         str | None = Query(default=None, alias='collectionName'),
        maxDoppler:             float | None = None,
        minDoppler:             float | None = None,
        maxFaradayRotation:     float | None = None,
        minFaradayRotation:     float | None = None,
        flightDirection:        str | None = None,
        flightLine:             str | None = None,
        frame:                  int | List[int] | None = None,
        granule_list:           str | List[str] | None = None,
        product_list:           str | List[str] | None = None,
        intersectsWith:         str | None = None,
        lookDirection:          str | None = None,
        offNadirAngle:          float | List[float] | None = None,
        platform:               str | None = None,
        polarization:           str | None = None,
        processingLevel:        str | None = Query(default=None, alias='processinglevel'),
        relativeOrbit:          int | List[int] | None = None,
        processingDate:         datetime | None = None,
        start:                  datetime | None = None,
        end:                    datetime | None = None,
        season:                 str | None = None,
        groupID:                str | None = None,
        insarStackId:           str | None = None,
        instrument:             str | None = None,
        collections:            str | List[str] | None = None,
        # Config parameters       Parser
        cmr_maturity:           str | None = Query(default=None, alias='maturity'),
        # host:                   str | None = None,
        provider:               str | None = None
    ):
        
        self.absoluteOrbit = absoluteOrbit
        self.asfFrame = asfFrame
        self.beamMode = string_to_list(beamMode)
        self.beamSwath = string_to_list(beamSwath)
        self.campaign = campaign if campaign else asfPlatform if asfPlatform != None else None
        self.maxDoppler = maxDoppler
        self.minDoppler = minDoppler
        self.maxFaradayRotation = maxFaradayRotation
        self.minFaradayRotation = minFaradayRotation
        self.flightDirection = flightDirection
        self.flightLine = flightLine
        self.frame = frame
        self.granule_list = string_to_list(granule_list)
        self.product_list = string_to_list(product_list)
        self.intersectsWith = intersectsWith
        self.lookDirection = lookDirection
        self.offNadirAngle = offNadirAngle
        self.platform = string_to_list(platform)
        self.polarization = string_to_list(polarization)
        self.processingLevel = string_to_list(processingLevel)
        self.relativeOrbit = relativeOrbit
        self.processingDate = processingDate
        self.start = start
        self.end = end
        self.season = map(lambda x: int(x), string_to_list(season)) if season is not None else None
        self.groupID = string_to_list(groupID)
        self.insarStackId = insarStackId
        self.instrument = instrument
        
        args = [(key, item) for key, item in locals().items() if not key in ['cmr_maturity', 'collectionName', 'asfPlatform', 'config', 'session', 'collections']]
        
        asf.ASFSearchOptions.__init__(**dict(args))

        self.maxResults = None if (granule_list != None or product_list != None) else maxResults
        config = load_maturity_config(cmr_maturity)
        self.host = config['host']
        self.session = asf.ASFSession()
        for key, val in config['headers'].items():
            # logging.warn(f"{key}, {val}")
            self.session.headers.update({key: val})
            
        self.provider = provider

def string_to_list(param: List[str] | str | None):
    if param is not None:
        if ',' in param:
            response = param.split(',')
            logging.warning(response)
            return response
        else:
            return param
