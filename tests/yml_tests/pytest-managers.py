from test_url_manager import test_URL_Manager
from test_missionList_manager import test_mission_list
from test_dateParser_manager import test_date_parser
from test_baseline_manager import test_baseline
from test_WKTUtils import test_filesToWKT, test_repairWKT
from fastapi.testclient import TestClient

from SearchAPI.application.application import app

client = TestClient(app=app, base_url='http://127.0.0.1:8080')
##########################
## SearchAPI Main tests ##
##########################
def test_URLManagerSearch(**args):
    test_URL_Manager(client=client, **args)

def test_MissionListEndpoint(**args):
    test_mission_list(client=client, **args)

def test_DateParserEndpoint(**args):
    test_date_parser(client=client, **args)

def test_BaselineEndpoint(**args):
    test_baseline(client=client, **args)

###########################
## WKTUtils Single tests ##
###########################
def test_FilesToWKTEndpoint(**args):
    test_filesToWKT(client=client, **args)

def test_RepairWKTEndpoint(**args):
    test_repairWKT(client=client, **args)
