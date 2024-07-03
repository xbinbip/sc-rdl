from zeep import Client
from zeep.transports import Transport
from requests import Response, Session
from requests.adapters import HTTPAdapter, Retry
import time
from zeep import helpers
from dotenv import load_dotenv, find_dotenv, set_key
import os

from datetime import datetime, timezone, timedelta
timezone_offset = 3.0  # Pacific Standard Time (UTC−08:00)
tzinfo = timezone(timedelta(hours=timezone_offset))
datetime_format = "%Y-%m-%d %H:%M:%S.%f%z"

load_dotenv()

# хелперы

def pprint_dt(dt):
    print(dt.strftime("%d.%m.%Y %H:%M:%S"))
    pass

class dotdict(dict):
    """dot.notation access to dictionary attributes"""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def compare_car_number(car_number1: str, car_number2: str) -> bool:
    c1 = car_number1.replace(" ", "").capitalize()
    c2 = car_number2.replace(" ", "").capitalize()
    return c1 == c2

spic_status = {
    'logged_in': False,
    'session_info': {
        'SessionId': os.getenv("SPIC_SESSION_ID") or None,
        'Expiring': os.getenv("SPIC_SESSION_EXPIRING") or datetime.now(tzinfo)
    }
}

dotenv_file = find_dotenv()

login = os.getenv("SPIC_LOGIN")
password = os.getenv("SPIC_PASSWORD")

def is_expired(date: datetime) -> bool:
    if (not date):
        return True
    return date < datetime.now(tzinfo)

def update_dotenv_creds(sessid: str, expiring: str) -> None:
    set_key(dotenv_file, "SPIC_SESSION_ID", sessid)
    set_key(dotenv_file, "SPIC_SESSION_EXPIRING", str(expiring))
    pass



base_url2 = "http://spic.scout365.ru:8081"
base_url = "http://login.scout-gps.ru"

object_type_id = {
    "transport": "0F1E3A4A-88F5-4166-9BE8-76033DD85D08",
    "terminal": "0783BE26-6398-480C-A88F-871438A01C36",
    "teminal_profile": "54E3C5C5-7EFE-49B9-AE0E-F8C44D52FA36",
}


login_params = {
    "Login": login,
    "Password": password,
    "TimeZoneOlsonId": "Asia/Yekaterinburg",
    "CultureName": "ru-ru",
    "UiCultureName": "ru-ru",
}


def soap_url(address: str) -> str:
    return base_url + "/spic/" + address + "/soap?wsdl"


soapLogin = soap_url("auth")
soapUnits = soap_url("Units")
soapOnlineDataService = soap_url("OnlineDataService")

session = Session()
spic_transport: Transport = None
wsdl_retries = Retry(total=5, backoff_factor=1, status_forcelist=[404])
session.mount("http://", HTTPAdapter(max_retries=wsdl_retries))

login_client = Client(soapLogin)
units_client = None

def old_login_check()-> bool:
    if(spic_status['session_info']['SessionId'] is None): return False
    if(is_expired(spic_status['session_info']['Expiring'])): return False
    return True

def login(login_client = login_client, login_params = login_params) -> dict:
    try:
        global spic_transport, spic_status
        if (old_login_check()):
            session.headers = {"ScoutAuthorization": spic_status['session_info']['SessionId']}
            spic_transport = Transport(session=session, timeout=(5, 30))
            print(f"Successful login attempt. Not expired. Session ID: {spic_status['session_info']['SessionId']}")
            spic_status['logged_in'] = True
            return {'ExpireDate': spic_status['session_info']['Expiring'],
                    'SessionId': spic_status['session_info']['SessionId']}
        resp = login_client.service.Login(login_params)
        time.sleep(1) #TODO Костыль, сервер что-то не успевает
        if "SessionId" in resp:
            session_id = resp["SessionId"]
            expiring = resp["ExpireDate"]
            spic_status = {'logged_in': True, 'session_info': {'SessionId': session_id, 'Expiring': expiring}}
            update_dotenv_creds(session_id, expiring)
            session.headers = {"ScoutAuthorization": session_id}
            spic_transport = Transport(session=session, timeout=(5, 30))
            print(f"Successful login attempt. Session ID: {session_id}") #DELETE ME
            return {'ExpireDate': expiring, 'SessionId': session_id}
        else:
            raise Exception("Login failed")
    except Exception as e:
        #TODO Handle the exception, log the error, and return an appropriate response
        print(f"An error occurred in login function: {str(e)}")
        print(f"login_params: {login_params}")
        return {'ExpireDate': None, 'SessionId': None}
    
def logout():
    global spic_status
    spic_status = {'logged_in': False, 'session_info': {'SessionId': None, 'Expiring': None}}
    pass

def get_unit_list():
    global units_client
    try:
        if units_client is None:
            units_client = Client(soapUnits, transport=spic_transport)
        resp = units_client.service.GetAllUnits()
        if 'SpicUnit' in resp:
            zeep_object_data = resp['SpicUnit']
            return helpers.serialize_object(zeep_object_data, dict)
        else:
            raise ValueError('Invalid response from GetAllUnits')
    except Exception as e:
        print(f"An error occurred in get_unit_list function: {str(e)}")
        raise
def main():
    #TEST
    login()

    # units_client.wsdl.dump()
    online_data_client = Client(soapOnlineDataService, transport=spic_transport)
    a: Response = get_unit_list()
    print(a, file=open("units.txt", "a"))
    #b: Response = online_data_client.service.GetOnlineData()

    c = online_data_client.service.Subscribe(request={"UnitIds": "104540"})
    c
    sid = c["SessionId"]
    d = online_data_client.service.GetOnlineData(onlineDataSessionId=sid)
    d
    print(d, file=open("output.txt", "a"))
    online_data_client.service.Unsubscribe(onlineDataSessionId=sid)
    print("Done")
    pass

if __name__ == "__main__":
    main()