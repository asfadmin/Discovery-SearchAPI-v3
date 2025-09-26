# Base Script provided by Rudi and Kelsey
from io import BytesIO
import os
import sys
import math
import json
import tempfile
from time import perf_counter
from typing import Literal
import pyproj
import lxml.etree as et
import imagesize
import shapely
from shapely import Point, LineString, LinearRing
from shapely.ops import transform
from shapely.geometry.base import BaseGeometry
from .logger import api_logger
from collections import deque
from osgeo import ogr, osr, gdal
def kml2geometry(kml_file):
    """Extract geometry from KML file"""

    ### Read KML file
    # parser = et.XMLParser()
    doc = et.ElementTree(et.fromstring(kml_file)) #, parser)

    ### Read coordinates
    ns0 = {'ns0': 'http://www.google.com/kml/ext/2.2'}
    ns_all = dict(list(ns0.items()))
    pts = doc.xpath('/kml/Document/GroundOverlay/' \
        'ns0:LatLonQuad/coordinates', namespaces=ns_all)[0].text.split(' ')
    point_count = len(pts)
    for i in range(point_count):
        pts[i] = pts[i].replace(',',' ')

    ### Put the vertices into a linear ring
    if point_count == 4:
        linear_ring = \
            f'LINEARRING ({pts[0]}, {pts[1]}, {pts[2]}, {pts[3]}, {pts[0]})'
    elif point_count == 5:
        linear_ring = \
            f'LINEARRING ({pts[0]}, {pts[1]}, {pts[2]}, {pts[3]}, {pts[4]})'
    else:
        print('Cannot figure out coordinates!')
        sys.exit(1)
    gcs_geometry = shapely.from_wkt(linear_ring)

    return gcs_geometry


def crosses_dateline(gcs_geometry):
    """Check whether polygon cross dateline"""

    intersects = False
    bounds = list(gcs_geometry.bounds)
    diff = bounds[2] - bounds[0]
    if bounds[0] < 0.0 and bounds[2] > 0.0 and diff > 180.0:
        intersects = True

    return intersects


def get_map_info(gcs_geometry):
    """Determine map EPSG from geometry"""

    ### Determine bounding coordinates
    centroid = gcs_geometry.centroid
    latitude = shapely.get_y(centroid)
    longitude = -179.0
    bounds = list(gcs_geometry.bounds)

    ### Determine EPSG based on bounding latitude
    epsg = 4326
    if bounds[1] >= -80.0 and bounds[3] <= 84.0:
        zone = math.floor((longitude + 180) / 6 + 1)
        if latitude > 0:
            epsg = int(32600 + zone)
        else:
            epsg = int(32700 + zone)
    elif bounds[3] > 84.0:
        epsg = 3413
    elif bounds[1] < -80.0:
        epsg = 3976

    return epsg, bounds


def project2map(shape, epsg) -> shapely.Geometry:
    """Reproject geographic shape into a map projection"""

    gcs_epsg = pyproj.CRS('EPSG:4326')
    map_epsg = pyproj.CRS(f'EPSG:{epsg}')
    project = pyproj.Transformer.from_crs(gcs_epsg, map_epsg,
        always_xy=True).transform

    return transform(project, shape)


def project2geo(shape, epsg):
    """Reproject a map projected shape into geographic coordinates"""
    # osr.SpatialReference.GetCoordinateEpoch()
    gcs_epsg = pyproj.CRS('EPSG:4326')
    map_epsg = pyproj.CRS(f'EPSG:{epsg}')
    project = pyproj.Transformer.from_crs(map_epsg, gcs_epsg,
        always_xy=True).transform

    return transform(project, shape)


def get_dateline_polygon(gcs_geometry):
    """Insert vertices to the polygon over the dateline"""

    (epsg, bounds) = get_map_info(gcs_geometry)
    gcs_dateline = LineString([(180,bounds[3]),(180,bounds[1])])
    map_dateline = project2map(gcs_dateline, epsg)
    map_geometry = project2map(gcs_geometry, epsg)

    points = []
    indices = []
    intersect_points = []
    point_count = shapely.get_num_points(map_geometry)
    line_count = point_count - 1
    for i in range(point_count):
        points.append(shapely.get_point(map_geometry, i))
    for i in range(line_count):
        line = LineString([points[i], points[i+1]])
        point = line.intersection(map_dateline)
        if point.wkt != 'LINESTRING Z EMPTY' and point.wkt != 'LINESTRING EMPTY':
            intersect_points.append(point)
            indices.append(i+1)
    index_count = len(indices)
    for i in range(index_count):
        index = indices[i] + i
        points[index:index] = [intersect_points[i]]
    map_dateline_geometry = LinearRing(points)
    gcs_dateline_geometry = project2geo(map_dateline_geometry, epsg)

    return gcs_dateline_geometry


def extract_geometry_coordinates(gcs_geometry):
    """Extract geometry coordinates"""

    longitudes, latitudes = gcs_geometry.coords.xy
    latitude = list(latitudes)
    longitude = list(longitudes)

    return latitude, longitude


def wrapped_dateline_polygon(gcs_geometry, wrap=True):
    """Calculate a wrapped version of the dateline polygon"""

    ### Extract coordinates from the geometry
    (latitude, longitude) = extract_geometry_coordinates(gcs_geometry)
    point_count = shapely.get_num_coordinates(gcs_geometry)

    ### Cull dateline coordinates
    for i in reversed(range(point_count)):
        if math.isclose(longitude[i], 180.0, abs_tol=0.001) or \
            math.isclose(longitude[i], -180.0, abs_tol=0.001):
            del latitude[i]
            del longitude[i]
        elif wrap:
            if longitude[i] < 0:
                longitude[i] += 360.0

    ### Build a wrapped geometry
    point_count = len(latitude)
    vertices = []
    for i in range(point_count):
        vertices.append(Point(longitude[i],latitude[i]))
    dateline_geometry = LinearRing(vertices)

    return dateline_geometry

def rotate_points(latitude, longitude, orbit_direction: str):
    orbit_offset = 2 if orbit_direction == 'ascending' else  1
    latitude.pop()
    longitude.pop()
    longitude = deque(longitude)
    longitude.rotate(orbit_offset)
    latitude = deque(latitude)
    latitude.rotate(orbit_offset)
    latitude = list(latitude)
    longitude = list(longitude)

    return latitude, longitude


def determine_corner(gcs_geometry, dateline, png_file, orbit_direction) -> tuple[BaseGeometry, dict]:
    """Determine corner of the first vertex of geometry"""

    ### Get PNG image size
    (width, height) = imagesize.get(png_file)

    ### Get corner geometry
    if dateline:
        gcs_corner_geometry = wrapped_dateline_polygon(gcs_geometry)
    else:
        gcs_corner_geometry = gcs_geometry

    ### Is the point order counterclockwise?
    is_ccw = False
    if shapely.is_ccw(gcs_corner_geometry):
        print('Reversing point order ...')
        gcs_corner_geometry = gcs_corner_geometry.reverse()
        if dateline:
            is_ccw = True

    gcs_corner_geometry
    ### Get coordinates and bounds from geometry
    (latitude, longitude) = extract_geometry_coordinates(gcs_corner_geometry)
    (min_longitude, min_latitude, max_longitude, max_latitude) = \
        gcs_corner_geometry.bounds


    ### Get corner coordinates sorted out
    corners = {}
    if math.isclose(longitude[0], min_longitude, abs_tol=0.0001) and \
        math.isclose(latitude[1], max_latitude, abs_tol=0.0001) and \
        math.isclose(longitude[2], max_longitude, abs_tol=0.0001) and \
        math.isclose(latitude[3], min_latitude, abs_tol=0.0001):
        if orbit_direction == 'ascending':
            print('Ascending - upper left corner')
        elif orbit_direction == 'descending':
            print('Descending - lower left corner')

        
        latitude, longitude = rotate_points(latitude, longitude, orbit_direction)
        # corners['ul'] = f'0 0 {longitude[0]} {latitude[0]}'
        # corners['ur'] = f'{width} 0 {longitude[1]} {latitude[1]}'
        # corners['lr'] = f'{width} {height} {longitude[2]} {latitude[2]}'
        # corners['ll'] = f'0 {height} {longitude[3]} {latitude[3]}'

        corners['ur'] = gdal.GCP(width, 0.0, 0.0, longitude[1],latitude[1])
        corners['lr'] = gdal.GCP(width, height, 0.0, longitude[2],latitude[2])
        corners['ll'] = gdal.GCP(0.0, height, 0.0, longitude[3], latitude[3])
        corners['ul'] = gdal.GCP(0.0, 0.0, 0.0, longitude[0], latitude[0])

    ### Ascending upper right corner or descending upper left corner
    elif math.isclose(latitude[0], max_latitude, abs_tol=0.0001) and \
        math.isclose(longitude[1], max_longitude, abs_tol=0.0001) and \
        math.isclose(latitude[2], min_latitude, abs_tol=0.0001) and \
        math.isclose(longitude[3], min_longitude, abs_tol=0.0001):
        if orbit_direction == 'ascending':
            print('Ascending - upper right corner')
        elif orbit_direction == 'descending':
            print('Descending - upper left corner')

        latitude, longitude = rotate_points(latitude, longitude, orbit_direction)
        # corners['ul'] = f'0 0 {longitude[3]} {latitude[3]}'
        # corners['ur'] = f'{width} 0 {longitude[0]} {latitude[0]}'
        # corners['lr'] = f'{width} {height} {longitude[1]} {latitude[1]}'
        # corners['ll'] = f'0 {height} {longitude[2]} {latitude[2]}'

        corners['lr'] = gdal.GCP(width, height, 0.0, longitude[1],latitude[1])
        corners['ll'] = gdal.GCP(0.0, height, 0.0, longitude[2],latitude[2])
        corners['ul'] = gdal.GCP(0.0, 0.0, 0.0, longitude[3], latitude[3])
        corners['ur'] = gdal.GCP(width, 0.0, 0.0, longitude[0], latitude[0])
        

    ### Ascending lower right corner or descending upper right corner
    elif math.isclose(longitude[0], max_longitude, abs_tol=0.0001) and \
        math.isclose(latitude[1], min_latitude, abs_tol=0.0001) and \
        math.isclose(longitude[2], min_longitude, abs_tol=0.0001) and \
        math.isclose(latitude[3], max_latitude, abs_tol=0.0001):
        if orbit_direction == 'ascending':
            print('Ascending - lower right corner')
        elif orbit_direction == 'descending':
            print('Descending - upper right corner')

        latitude, longitude = rotate_points(latitude, longitude, orbit_direction)
        # corners['ul'] = f'0 0 {longitude[2]} {latitude[2]}'
        # corners['ur'] = f'{width} 0 {longitude[3]} {latitude[3]}'
        # corners['lr'] = f'{width} {height} {longitude[0]} {latitude[0]}'
        # corners['ll'] = f'0 {height} {longitude[1]} {latitude[1]}'

        corners['ll'] = gdal.GCP(0.0, height, 0.0, longitude[1],latitude[1])
        corners['ul'] = gdal.GCP(0.0, 0.0, 0.0, longitude[2],latitude[2])
        corners['ur'] = gdal.GCP(width, 0.0, 0.0, longitude[3], latitude[3])
        corners['lr'] = gdal.GCP(width, height, 0.0, longitude[0], latitude[0])
        

    ### Ascending lower left corner or descending lower right corner
    else: # math.isclose(latitude[0], min_latitude, abs_tol=0.0001) and \
        # math.isclose(longitude[1], min_longitude, abs_tol=0.0001) and \
        # math.isclose(latitude[2], max_latitude, abs_tol=0.0001) and \
        # math.isclose(longitude[3], max_longitude, abs_tol=0.0001):
        if orbit_direction == 'ascending':
            print('Ascending - lower left corner')
        elif orbit_direction == 'descending':
            print('Descending - lower right corner')
        latitude, longitude = rotate_points(latitude, longitude, orbit_direction)
        corners['ul'] = gdal.GCP(0.0, 0.0, 0.0, longitude[1],latitude[1])
        corners['ur'] = gdal.GCP(width, 0.0, 0.0, longitude[2],latitude[2])
        corners['lr'] = gdal.GCP(width, height, 0.0, longitude[3], latitude[3])
        corners['ll'] = gdal.GCP(0.0, height, 0.0, longitude[0], latitude[0])
        
        # corners['ul'] = f'0 0 {longitude[1]} {latitude[1]}'
        # corners['ur'] = f'{width} 0 {longitude[2]} {latitude[2]}'
        # corners['lr'] = f'{width} {height} {longitude[3]} {latitude[3]}'
        # corners['ll'] = f'0 {height} {longitude[0]} {latitude[0]}'

    ### Reverse dateline if needed
    if is_ccw:
        gcs_geometry = gcs_geometry.reverse()

    return gcs_geometry, corners


def nisar_browse_kml(kml_file: str, png_file: BytesIO, output_file: str, orbit_direction: Literal['ascending', 'descending']):
    """Generate a NISAR browse PNG image"""

    ### Get geometry from KML file
    gcs_geometry = kml2geometry(kml_file)

    ### Check for dateline crossing and fix it if needed
    dateline = crosses_dateline(gcs_geometry)
    if dateline:
        print('Polygon crosses International Dateline')
        gcs_geometry = get_dateline_polygon(gcs_geometry)

    ### Determine which corner the first coordinate is
    b = png_file.read()
    (gcs_geometry, corners) = \
        determine_corner(gcs_geometry, dateline, png_file, orbit_direction)
    # print('Corners')
    # print(json.dumps({corner_name: corner.serialize() for corner_name, corner in corners.items()}, indent=2))

    ### Apply corner coordinates
    tmp = tempfile.NamedTemporaryFile(delete_on_close=False)
    
    # Open the file for writing.
    with open(tmp.name, 'wb') as f:
        # b = png_file.read()
        f.write(b)

        # gdal_translate = f'gdal_translate -gcp {corners["ul"]} -gcp {corners["ur"]} -gcp {corners["lr"]} -gcp {corners["ll"]} -a_srs EPSG:3857 ' \
        # f"{tmp.name} {output_file}"

        gdal.Translate(
            destName=output_file,
            srcDS=tmp.name,
            options=gdal.TranslateOptions(
                GCPs=[corners['ll'], corners['ul'], corners['ur'], corners['lr'], ],
                outputSRS='EPSG:3857',
                format='png',
            )
        )
        # start = perf_counter()
        # os.system(gdal_translate)
        # api_logger.info(perf_counter() - start)
        # cmd = f"gdalwarp -t_srs EPSG:3857 -overwrite " \
        #     f"{output_file} 2{output_file}"
        # start = perf_counter()
        gdal.Warp(destNameOrDestDS=f'2{output_file}', srcDSOrSrcDSTab=output_file, options=gdal.WarpOptions(
            format='png',
            dstSRS='EPSG:4326',
            srcSRS="EPSG:3857"
        ))
        
        # os.system(cmd)
        # api_logger.info(perf_counter() - start)
    print(f'\n\nGeometry: {gcs_geometry}')
