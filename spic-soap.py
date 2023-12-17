from zeep import Client
from zeep.transports import Transport
from requests import Response, Session
# хелперы


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def compare_car_number(car_number1: str, car_number2: str) -> bool:
    c1 = ''.join(car_number1.split()).capitalize()
    c2 = ''.join(car_number2.split()).capitalize()
    return (c1 == c2)


base_url2 = 'http://spic.scout365.ru:8081'
base_url = 'http://login.scout-gps.ru'

object_type_id = {'transport': "0F1E3A4A-88F5-4166-9BE8-76033DD85D08",
                  'terminal': "0783BE26-6398-480C-A88F-871438A01C36",
                  'teminal_profile': "54E3C5C5-7EFE-49B9-AE0E-F8C44D52FA36"}


login_params = {
    "Login": "kgm@redlineekb.ru",
    "Password": "5Amxqv",
    "TimeZoneOlsonId": "Asia/Yekaterinburg",
    "CultureName": "ru-ru",
    "UiCultureName": "ru-ru"
}


def soap_url(address: str) -> str:
    return base_url + '/spic/' + address + '/soap?wsdl'


soapLogin = soap_url('auth')
soapUnits = soap_url('Units')
soapOnlineDataService = soap_url('OnlineDataService')

session = Session()

login_client = Client(soapLogin)


def login() -> str:
    resp = login_client.service.Login(login_params)
    return resp['SessionId']


session_id = login()
session.headers = {"ScoutAuthorization": session_id}
transport = Transport(session=session)

units_client = Client(soapUnits, transport=transport)
units_client.wsdl.dump()
online_data_client = Client(soapOnlineDataService)
a: Response = units_client.service.GetAllUnits()
