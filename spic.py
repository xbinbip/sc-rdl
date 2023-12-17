from requests import get, post
import datetime
# !! Костыль !!
TZ = '0500'

# хелперы


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def dt_to_ms(date: datetime) -> float:
    return float(date.timestamp())


def dt_to_jms(date: datetime) -> str:
    ms = int(dt_to_ms(date)) * 1000
    st = f'/Date({ms}+{TZ})/'
    return st


def ms_to_dt(ms: float) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(ms)


def jms_to_dt(date: str):
    if '+' in date:
        ms = int(date[6:-7])
    else:
        ms = int(date[6:-2:])
    return datetime.datetime.fromtimestamp(ms / 1000)


def compare_car_number(car_number1: str, car_number2: str) -> bool:
    c1 = ''.join(car_number1.split()).capitalize()
    c2 = ''.join(car_number2.split()).capitalize()
    return (c1 == c2)


base_url2 = 'http://spic.scout365.ru:8081'
base_url = 'http://login.scout-gps.ru'

object_type_id = {'transport': "0F1E3A4A-88F5-4166-9BE8-76033DD85D08",
                  'terminal': "0783BE26-6398-480C-A88F-871438A01C36",
                  'teminal_profile': "54E3C5C5-7EFE-49B9-AE0E-F8C44D52FA36"}

url_list = {
    'login': '/spic/auth/rest/Login',
    'get_all_units_paged': '/spic/units/rest/getAllUnitsPaged',
    'unit_ids': '/spic/units/rest/unitIds',
    'get_units': '/spic/units/rest/getUnits',
    'unit_groups': '/spic/unitGroups/rest/',
    'get_drivers': '/spic/drivers/rest/getDrivers',
    'get_avail_drivers': '/spic/drivers/rest/getAvailableDrivers',
    'get_all_units': '/spic/units/rest/getAllUnits',
    'get_avail_reports': '/spic/reports/rest/GetAvailableReports',
    'build_reports': '/spic/reports/rest/BuildReports',
    'subscribe': '/spic/OnlineDataService/rest/Subscribe',
    'get_online_data': '/spic/OnlineDataService/rest/GetOnlineData',
    'unsubscribe': '/spic/OnlineDataService/rest/Unsubscribe',
    'subscribe_sensors': '/spic/OnlineDataWithSensorsService/rest/Subscribe',
    'get_onnline_data_sensors':
        '/spic/OnlineDataWithSensorsService/rest/GetOnlineData',
    'unsubscribe_sensors':
        '/spic/OnlineDataWithSensorsService/rest/Unsubscribe',
    'start_statistics_session':
        '/spic/StatisticsController/rest/StartStatisticsSession',
    'start_build': '/spic/StatisticsController/rest/StartBuild',
    'cancel_statistics_session':
        '/spic/StatisticsController/rest/CancelStatisticsSession',
    'add_statistics_request':
        '/spic/NavigationFiltration/rest/AddStatisticsRequest',
    'get_statistics':
        '/spic/AnalogSensor/rest/GetStatistics',
    'add_statistics_request_analog':
        '/spic/AnalogSensor/rest/AddStatisticsRequest',
}

urls = dotdict(url_list)
for k, v in urls.items():
    urls[k] = base_url + v

auth_header = {
    'accept': 'application/json; charset=utf-8',
    'Content-Type': 'application/json'
}
req_header = {
    'accept': '*/*',
    'Content-Type': 'application/json',
    'ScoutAuthorization': None
}

login_params = {
    "Login": "kgm@redlineekb.ru",
    "Password": "5Amxqv",
    "TimeZoneOlsonId": "Asia/Yekaterinburg",
    "CultureName": "ru-ru",
    "UiCultureName": "ru-ru"
}

session_id = None

local_object_list = []


def authorize():
    response = post(urls.login, headers=auth_header, json=login_params)

    if response.ok:
        global session_id
        session_id = response.json().get('SessionId')
        # is_authorized = response.json().get('IsAuthorized')
        # expiration_date = jms_to_dt(response.json().get('ExpireDate'))
        req_header['ScoutAuthorization'] = session_id
        return response.json()
    else:
        raise (EnvironmentError)


def test2():  # хз чё тестил, удалить?
    template_id = "4ddd4734-64c9-4143-b951-b828d5c72578"
    rep_id = "fc8ec966-3779-47d7-b579-9514541b0566"
    output_format = 'pdf'
    targets = [test_unit_id]
    beg_date = dt_to_jms(datetime.datetime(
        2021, 10, 4, 0, 0, 0) + datetime.timedelta(hours=2))
    end_date = dt_to_jms(datetime.datetime(
        2021, 10, 4, 23, 59, 59) + datetime.timedelta(hours=2))
    report_target_type = 'Unit'
    report_taget_cardinality_type = 'One'
    params = {
        "ReportTemplateId": template_id,
        "ReportType": rep_id,
        "ReportTargetType": {
            "Value": report_target_type
        },
        "ReportTargetCardinalityType": {
            "Value": report_taget_cardinality_type
        },
        "OutputFormat": {
            "Value": output_format
        },
        "Targets": targets,
        "BeginDateTime": beg_date,
        "EndDateTime": end_date,
        "Emails": [
            "xbinbip@gmail.com"
        ]
    }
    print(beg_date)
    return post(urls.build_reports, headers=req_header, json=params)

# mixed


def find_car_by_cn(car_number: str, units_list: list[dict]) -> str:
    for obj in units_list:
        if 'StateNumber' in obj:
            if (compare_car_number(obj['StateNumber'], car_number)):
                return obj
        else:
            print(f'У объекта - {obj['Description']}'
                  f', отсутствует поле с Госномером')
            pass

# Запросы к СПИК


def get_avail_reports():
    resp = get(urls.get_avail_reports, headers=req_header, timeout=5)
    if resp.ok:
        return resp
    else:
        print(
            f'Не удалось получить список отчётов:'
            f'Ошибка {resp.status_code} - {resp.reason}')


def get_all_units():
    resp = get(urls.get_all_units, headers=req_header, timeout=5)
    if resp.ok:
        return resp.json()['Units']
    else:
        print(
            f'Не удалось получить список объектов:'
            f'Ошибка {resp.status_code} - {resp.reason}')


def get_online_data(id: int):
    resp = get(urls.get_online_data, headers=req_header, timeout=5)
    if resp.ok:
        return resp.json()
    else:
        print(
            f'Не удалось получить данные по объекту {id}'
            f'Ошибка {resp.status_code} - {resp.reason}')


test_unit_id = 14095


def test():
    local_object_list = get_all_units()
    car_id = find_car_by_cn("КА599 66", local_object_list)['UnitId']
    return get_online_data(car_id)


print(authorize())
