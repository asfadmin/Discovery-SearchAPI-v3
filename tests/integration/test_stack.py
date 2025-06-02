import boto3
from urllib import parse as param_parse
import asf_search as asf
import os

cf_client = boto3.client('cloudformation', region_name=os.getenv('CDK_DEFAULT_REGION', 'us-east-1'))
cf_response = cf_client.describe_stacks(StackName='SearchAPI-V3-Stack-Staging')
rest_api_url = cf_response['Stacks'][0]['Outputs'][0]['OutputValue']
session = asf.ASFSession()

cwd = os.getcwd()
geojson_test_file_path= os.path.join(cwd, 'tests/integration/', 'elvey.geojson')
kml_test_file_path = os.path.join(cwd, 'tests/yml_tests/Resources/kmls_valid/', '3D_coords.kml')
shp_test_file_path = os.path.join(cwd, 'tests/yml_tests/Resources/shps_valid/', 'NED1_F.shp')
zip_test_file_path = os.path.join(cwd, 'tests/yml_tests/Resources/zips_valid/', 'NED1_F.zip')

basic_search_params = {
    'maxResults': 250,
    'dataset': asf.DATASET.SENTINEL1,
    'output': 'jsonlite',
}

baseline_search_params = {
    'maxResults': 250,
    'reference': 'S1A_IW_SLC__1SSV_20150601T010209_20150601T010236_006173_00808F_20A0',
    'output': 'jsonlite',
}

wkt_params = {
    'wkt': 'POINT(-147.8493 64.8595)'
}

params_endpoint = f'{rest_api_url}services/search/param'
baseline_endpoint = f'{rest_api_url}services/search/baseline'
wkt_endpoint = f'{rest_api_url}services/utils/wkt'
files_wkt_endpoint = f'{rest_api_url}services/utils/files_to_wkt'

### HEALTH ENDPOINT TEST
def test_health_endpoint():
    response = session.get(rest_api_url)
    response.raise_for_status()

    assert response.status_code == 200, f'Non-200 status code from health endpoint: \nstatus code: {response.status_code}\nresponse: {response.text}'

### PARAMS ENDPOINT TESTS
def test_params_endpoint_get():
    params = param_parse.urlencode(basic_search_params, doseq=False)
    
    response = session.get(f'{params_endpoint}?{params}')
    response.raise_for_status()

    assert response.status_code == 200, f'Non-200 status code from GET params endpoint: \nstatus code: {response.status_code}\nresponse: {response.text}'

def test_params_endpoint_post_data():
    response = session.post(params_endpoint, data=basic_search_params)
    response.raise_for_status()

    assert response.status_code == 200, f'Non-200 status code from POST params endpoint (data): \nstatus code: {response.status_code}\nresponse: {response.text}'

def test_params_endpoint_post_json():
    response = session.post(params_endpoint, json=basic_search_params)
    response.raise_for_status()

    assert response.status_code == 200, f'Non-200 status code from params POST endpoint (json): \nstatus code: {response.status_code}\nresponse: {response.text}'

### BASELINE ENDPOINT TESTS
def test_baseline_endpoint_get():
    params = param_parse.urlencode(baseline_search_params, doseq=False)
    
    response = session.get(f'{baseline_endpoint}?{params}')
    response.raise_for_status()

    assert response.status_code == 200, f'Non-200 status code from baseline GET endpoint: \nstatus code: {response.status_code}\nresponse: {response.text}'

def test_baseline_endpoint_post_data():
    response = session.post(baseline_endpoint, data=baseline_search_params)
    response.raise_for_status()

    assert response.status_code == 200, f'Non-200 status code from baseline POST endpoint (data): \nstatus code: {response.status_code}\nresponse: {response.text}'

def test_baseline_endpoint_post_json():
    response = session.post(baseline_endpoint, json=baseline_search_params)
    response.raise_for_status()

    assert response.status_code == 200, f'Non-200 status code from baseline POST endpoint (json): \nstatus code: {response.status_code}\nresponse: {response.text}'

### WKT ENDPOINT TESTS
def test_wkt_endpoint_get():
    params = param_parse.urlencode(wkt_params, doseq=False)
    response = session.post(f'{wkt_endpoint}?{params}')
    response.raise_for_status()

    assert response.status_code == 200, f'Non-200 status code from baseline POST endpoint (data): \nstatus code: {response.status_code}\nresponse: {response.text}'

def test_wkt_endpoint_post_data():
    response = session.post(wkt_endpoint, data=wkt_params)
    response.raise_for_status()

    assert response.status_code == 200, f'Non-200 status code from baseline POST endpoint (data): \nstatus code: {response.status_code}\nresponse: {response.text}'

def test_wkt_endpoint_post_json():
    response = session.post(wkt_endpoint, json=wkt_params)
    response.raise_for_status()

    assert response.status_code == 200, f'Non-200 status code from baseline POST endpoint (data): \nstatus code: {response.status_code}\nresponse: {response.text}'

### WKT FILE UPLOAD TEST
def test_wkt_file_upload_endpoint_geojson():
    _wkt_file_upload_endpoint(geojson_test_file_path)

def test_wkt_file_upload_endpoint_kml():
    _wkt_file_upload_endpoint(kml_test_file_path)

def test_wkt_file_upload_endpoint_shp():
    _wkt_file_upload_endpoint(shp_test_file_path)

def test_wkt_file_upload_endpoint_zip():
    _wkt_file_upload_endpoint(zip_test_file_path)


def _wkt_file_upload_endpoint(file: str):
    files = {'files': open(file,'rb')}
    response = session.post(files_wkt_endpoint, files=files)
    response.raise_for_status()

    assert response.status_code == 200, f'Non-200 status code from files_to_wkt endpoint for file {file.split("/")[-1]}: \nstatus code: {response.status_code}\nresponse: {response.text}'
