from requests import get, post
import datetime

# !! Костыль !!
TZ = '0500'


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def dt_to_ms(date: datetime):
    return float(date.timestamp())


def dt_to_jms(date: datetime):
    ms = int(dt_to_ms(date)) * 1000
    st = f'/Date({ms}+{TZ})/'
    return st


def ms_to_dt(ms: float):
    return datetime.datetime.fromtimestamp(ms)


def jms_to_dt(date: str):
    if '+' in date:
        ms = int(date[6:-7])
    else:
        ms = int(date[6:-2:])
    return datetime.datetime.fromtimestamp(ms / 1000)


base_url2 = 'http://spic.scout365.ru:8081'
base_url = 'http://login.scout-gps.ru'

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
    'get_onnline_data_sensors': '/spic/OnlineDataWithSensorsService/rest/GetOnlineData',
    'unsubscribe_sensors': '/spic/OnlineDataWithSensorsService/rest/Unsubscribe',
    'start_statistics_session': '/spic/StatisticsController/rest/StartStatisticsSession',
    'start_build': '/spic/StatisticsController/rest/StartBuild',
    'cancel_statistics_session': '/spic/StatisticsController/rest/CancelStatisticsSession',
    'add_statistics_request': '/spic/NavigationFiltration/rest/AddStatisticsRequest',
    'get_statistics': '/spic/AnalogSensor/rest/GetStatistics',
    'add_statistics_request_analog': '/spic/AnalogSensor/rest/AddStatisticsRequest',
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
    'Content-Length': '8',
    'data': "",
    'ScoutAuthorization': None
}

login_params = {
    "Login": "kgm@redlineekb.ru",
    "Password": "5Amxqv",
    "TimeZoneOlsonId": "Asia/Yekaterinburg",
    "CultureName": "ru-ru",
    "UiCultureName": "ru-ru"
}

response = post(urls.login, headers=auth_header, json=login_params)

session_id = None
expiration_date = None

if response.ok:
    session_id = response.json().get('SessionId')
    is_authorized = response.json().get('IsAuthorized')
    expiration_date = jms_to_dt(response.json().get('ExpireDate'))
    req_header['ScoutAuthorization'] = session_id
else:
    raise(EnvironmentError)


def test():
    response = get(base_url + urls.get_all_units,
                   headers=req_header, timeout=5)
    return response.json()


def test2():
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


def get_avail_reports():
    resp = get(urls.get_avail_reports, headers=req_header)
    if resp.ok:
        return resp
    else:
        print(
            f'Не удалось получить список отчётов: Ошибка {resp.status_code} - {resp.reason}')


test_unit_id = 14095

print(response.json())
