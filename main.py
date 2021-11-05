import os
from pathlib import Path
import xml.etree.ElementTree as ET
from datetime import timedelta
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell

main_dir = Path(os.path.abspath(os.getcwd()))
in_dir = main_dir / 'in'
out_dir = main_dir / 'out'
input_format = '.xml'


def form_file_list():
    report_files = Path(in_dir).glob('**/О*' + input_format)
    sensor_files = Path(in_dir).glob('**/З*' + input_format)
    return list(zip(report_files, sensor_files))


file_list = form_file_list()


# HELPERS


def parse_time(time, delimeter=':'):
    return list(map(lambda x: int(x), time.split(delimeter)))


def format_td(td):
    _time = seconds_to_hours(td)
    h, m, s = [None, None, None]
    if (_time[0] < 10):
        h = f'0{_time[0]}'
    else:
        h = f'{_time[0]}'
    if (_time[1] < 10):
        m = f'0{_time[1]}'
    else:
        m = f'{_time[1]}'
    if (_time[2] < 10):
        s = f'0{_time[2]}'
    else:
        s = f'{_time[2]}'
    return f'{h}:{m}:{s}'


def seconds_to_hours(td):
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return [days * 24 + hours, minutes, seconds]


def int_str(st):
    return int(''.join(filter(str.isdigit, st)))


def float_str(st):
    _st = st.replace(',', '.')
    return round(float(''.join(filter(lambda x: str.isdigit(x) or x == '.', _st))), 2)


def time_to_float(hours, minutes, seconds=0):
    if (minutes == 0):
        return float(hours)
    else:
        return round((float(hours) + minutes / 60.0), 2)


def to_td(hours, minutes, seconds):
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)

# __HELPERS


class XmlReport():
    def __init__(self, path):
        self.path = path
        self.tree = None
        self.root = None
        self.__parse()

    def __parse(self):
        with open(self.path, mode='r', encoding="utf_8_sig") as xml:
            try:
                xml_temp = ET.parse(xml)
            except OSError as err:
                print("OS error: {0}".format(err))
            else:
                self.tree = xml_temp
                self.root = self.tree.getroot()

    def get_tag_text(self, root_index, text):
        return self.root[root_index].find(text).text

    def sensors_data(self):
        object_name = self.get_tag_text(1, 'UNITINFOTEXT')

        report_period = []
        report_period.append(self.get_tag_text(2, 'REPORTPERIODFROMDATE'))
        report_period.append(self.get_tag_text(2, 'REPORTPERIODFROMTIME'))
        report_period.append(self.get_tag_text(2, 'REPORTPERIODTODATE'))
        report_period.append(self.get_tag_text(2, 'REPORTPERIODTOTIME'))

        user = self.get_tag_text(3, 'UNITINFOTEXT')
        sensors_list = self.get_tag_text(4, 'UNITINFOTEXT')
        number_of_sensors = len(sensors_list.split(','))
        sensors_data = []
        for i in range(5, (5 + number_of_sensors)):
            sensor_name = self.get_tag_text(i, 'SUMMARYSENSORTEXT')
            activation_count = self.get_tag_text(
                i, 'SUMMARYACTIVATIONSCOUNTTEXT')
            active_time = self.get_tag_text(i, 'SUMMARYONDURATIONTEXT')
            inactive_time = self.get_tag_text(i, 'REPORTPERIODTOTIME')
            sensors_data.append(
                [sensor_name, activation_count, active_time, inactive_time])
        return [object_name, report_period, user, sensors_list, sensors_data]

    def fuel_data(self):
        object_name = self.get_tag_text(1, 'TEXT6')
        fuel_data = []
        sensor_indices = []
        sensor_end_indices = []
        total_fuel_consumption = []
        starting_fuel = []
        finish_fuel = []
        total_refuels = []
        mileage = []

        for i in range(0, (len(list(self.root)) - 1)):
            if self.get_tag_text(i, 'REPORTHEADERTEXT') == "Датчик":
                sensor_indices.append(i)

        for i in range(0, (len(list(self.root)) - 1)):
            if self.get_tag_text(i, 'REPORTHEADERTEXT') == "Уровень топлива в баке от времени":
                sensor_end_indices.append(i)

        for fuel in self.root.findall('./Table1/REPORTHEADERTEXT[.="Итоговый расход"]..'):
            total_fuel_consumption.append(
                fuel.find('./FUELEVENTSEVENTDATA').text)

        for ml in self.root.findall('./Table1/REPORTHEADERTEXT[.="Пробег"]..'):
            mileage.append(ml.find('./FUELEVENTSEVENTDATA').text)

        for fuel in self.root.findall('./Table1/REPORTHEADERTEXT[.="Начальный объём"]..'):
            starting_fuel.append(fuel.find('./FUELEVENTSEVENTDATA').text)
            finish_fuel.append(fuel.find('./FUELEVENTSADDRESSDATA').text)

        for fuel in self.root.findall('./Table1/REPORTHEADERTEXT[.="Объём заправок"]..'):
            total_refuels.append(
                fuel.find('./FUELEVENTSEVENTDATA').text)
            # кол-во сливов тутже

        for i in range(0, len(sensor_indices)):
            sensor_name = self.get_tag_text(sensor_indices[i], 'TEXT6')

            report_period = []
            report_period.append(self.get_tag_text(
                sensor_indices[i] + 1, 'REPORTPERIODFROMDATE'))
            report_period.append(self.get_tag_text(
                sensor_indices[i] + 1, 'REPORTPERIODFROMTIME'))
            report_period.append(self.get_tag_text(
                sensor_indices[i] + 1, 'REPORTPERIODTODATE'))
            report_period.append(self.get_tag_text(
                sensor_indices[i] + 1, 'REPORTPERIODTOTIME'))

            fuel_data.append([sensor_name, report_period, total_fuel_consumption[i],
                              starting_fuel[i], finish_fuel[i], total_refuels[i], mileage[i]])

        return [object_name, fuel_data]


class EngineHours():
    def __init__(self, data, wh_coeff=1):
        self.name = data[0]
        self.count = int(data[1])
        t1 = parse_time(data[2])
        t2 = parse_time(data[3])
        self.working_time = timedelta(
            hours=t1[0], minutes=t1[1], seconds=t1[2])
        self.inactive_time = timedelta(
            hours=t2[0], minutes=t2[1], seconds=t2[2])
        self.engine_hours = timedelta(
            seconds=(self.working_time.seconds * wh_coeff))


class ReportData():
    def __init__(self):
        self.object_name = None        # имя объекта
        self.user = ""
        self.start_date = None                 # дата начала отчёта
        self.end_date = None                   # дата окончания отчёта
        self.sensors = []                      # показания с датчиков по моточасам
        self.twh = None                           # Общее количество отработанных часов
        self.engine_hours = None                 # общие моточасы
        self.engine_hours_km = None               # моточасы в перерасчёте на километры
        self.mileage = None                       # фактический пробег
        self.total_fuel_consumption = None        # фактический расход топлива
        self.remaining_fuel_start = None         # топливо на начало отчёта
        self.remaining_fuel_end = None           # топливо на конец отчёта
        self.total_refuels = None                # общее количество заправленного
        self.fuel_consumption_mh = None               # раход на моточасы
        self.fuel_consumption_h = None                 # расход на часы
        self.sensors_data = []                  # подготовленные данные датчиков

    def fill(self, sensors_data, fuel_data):
        self.object_name = fuel_data[0]
        self.start_date = sensors_data[1][0] + " - " + sensors_data[1][1]
        self.end_date = sensors_data[1][2] + " - " + sensors_data[1][3]
        self.sensors = sensors_data[4]
        self.user = sensors_data[2]

        # eh_vibro = EngineHours(sensors_data[4][0])         # игнорируем ВИБРО
        # Моточасы до 1к
        eh_1 = EngineHours(sensors_data[4][1])
        # Моточасы от 1к до 2к
        eh_2 = EngineHours(sensors_data[4][2], 1.5)
        # Моточасы от 2к до 4к
        eh_3 = EngineHours(sensors_data[4][3], 3)
        _twh = eh_1.working_time.seconds + \
            eh_2.working_time.seconds + eh_3.working_time.seconds
        _ts = eh_1.working_time.seconds + eh_2.working_time.seconds * \
            1.5 + eh_3.working_time.seconds * 3
        wh, wm, ws = seconds_to_hours(timedelta(seconds=_twh))
        th, tm, ts = seconds_to_hours(timedelta(seconds=_ts))
        wh_float = time_to_float(wh, wm)
        eh_float = time_to_float(th, tm)  # моточасы в десятичной дроби
        eh_txt = [
            "до 1000 / 100%",
            "от 1001-2000 / 150%",
            "от 2001-4000 / 300%"
        ]
        eh_arr = [eh_1, eh_2, eh_3]
        for (idx, eh) in enumerate(eh_arr):
            wt_str = format_td(eh.working_time)
            eh_str = format_td(eh.engine_hours)
            _td = [eh.name, eh.count, wt_str, eh_str]
            _td.append(eh_txt[idx])
            self.sensors_data.append(_td)

        self.engine_hours = format_td(timedelta(seconds=_ts))
        self.twh = format_td(timedelta(seconds=_twh))
        self.mileage = int_str(fuel_data[1][1][6])
        self.total_fuel_consumption = float_str(fuel_data[1][1][2])
        self.remaining_fuel_start = float_str(fuel_data[1][1][3])
        self.remaining_fuel_end = float_str(fuel_data[1][1][4])
        self.total_refuels = float_str(fuel_data[1][1][5])
        # умножаем моточасы на 7
        self.engine_hours_km = round(eh_float * 7, 2)
        self.fuel_consumption_h = round(
            (self.total_fuel_consumption / wh_float), 2)
        self.fuel_consumption_mh = round(
            (self.total_fuel_consumption / eh_float), 2)

    def __str__(self):
        str = f"Пользователь: {self.user}\n"  \
            f"Имя объекта: {self.object_name}\n"  \
            f"Время отчёта: с {self.start_date} по {self.end_date}\n"  \
            f"Датчики:{self.sensors}\n"  \
            f"Общий расход топлива:{self.total_fuel_consumption} л. ,\
              средний:{self.fuel_consumption_h} л/ч,\
               средний-МЧ:{self.fuel_consumption_mh} л/мч\n"  \
              f"Общая заправка: {self.total_refuels} л.\n" \
              f"Топливо на начало\\конец смены:{self.remaining_fuel_start}л.\
              \\{self.remaining_fuel_end}л.\n"  \
              f"время в состоянии Вкл: {self.twh}\n"  \
              f"Моточасы: {self.engine_hours}\n"  \
              f"Моточасы в км: {self.engine_hours_km}\n"  \
              f"Пробег: {self.mileage} км"

        return str


reports = []
for files in file_list:
    rf = XmlReport(files[1])
    rs = XmlReport(files[0])

    report = ReportData()
    report.fill(rs.sensors_data(), rf.fuel_data())
    reports.append(report)


workbook = xlsxwriter.Workbook('test.xlsx')
workbook.formats[0].set_font_name('Tahoma')

worksheet = workbook.add_worksheet()

# Залить таблицу цветом
fill_format = workbook.add_format({
    'fg_color': '#fffafa',
    'border': 0


})

for i in range(35):
    worksheet.set_row(i, None, fill_format)

worksheet.insert_image('A1', './redsco.png')
# 6.35 примерное соотношение формата библиотеки к см
worksheet.set_row(3, 8.6 * 6.35, fill_format)

# _____Заголовок отчёта_____
report_header_format = workbook.add_format({
    'bold': 1,
    'border': 2,
    'font_size': 13,
    'align': 'center',
    'valign': 'vcenter',
    'fg_color': '#e0e0e0'  # светло-серый
})

worksheet.merge_range('A5:N5', "Отчёт по датчикам", report_header_format)

# _____Данные отчёта_____

report_text_format = workbook.add_format({
    'font_size': 10,
    'bold': 1,
    'font_name': 'Tahoma',
    'fg_color': '#fffff0',  # Ivory
    'border': 1
})

report_name_range = ['A6:B6', 'A7:B7', 'A8:B8', 'A9:B9']

data_data_range = ['C6:N6', 'C7:N7', 'C8:N8', 'C9:N9']

data_column_names = ['Объект', 'Период отчёта', 'Пользователь', 'Датчики']

for rg in data_data_range:
    worksheet.merge_range(rg, 'text', report_text_format)

for rg, name in zip(report_name_range, data_column_names):
    worksheet.merge_range(rg, name, report_text_format)


# _____Данные датчиков_____

#  Заголовок
sensors_header_format = workbook.add_format({
    'bold': 1,
    'font_name': 'Tahoma',
    'border': 2,
    'font_size': 13,
    'align': 'center',
    'valign': 'vcenter',
    'fg_color': '#ffcc66'  # оранжевый
})

worksheet.merge_range('A11:N11', "МОТОЧАСЫ Статистика", sensors_header_format)

# Заголовки колонок
sensors_row_names_format = workbook.add_format({
    'font_size': 10,
    'bold': 0,
    'font_name': 'Georgia',
    'fg_color': '#dbe5f1',
    'border': 1,
    'align': 'center',
    'valign': 'vcenter',
    'text_wrap': True
})

sensor_column_headers = [
    'Объект',
    'Гос.номер',
    'Датчик',
    'Кол-во срабатываний',
    'Время в стостоянии "Вкл"',
    'Моточасы',
    'Обороты\n/Коэффициент',
    'Общий расход топлива, л / Расход топлива л/ч',
    'Общий расход топлива, л / Расход топлива л/мч',
    'Остаток топливо на начало смены,л',
    'Общая заправка топлива за смену',
    'Остаток топлива на конец смены, л',
    'Моточасы в км (7 км для гусеничной техники)',
    'Пробег, км'
]

worksheet.set_row(11, 60, fill_format)
worksheet.write_row('A12', sensor_column_headers, sensors_row_names_format)

# данные датчиков
sensors_row_data_format = workbook.add_format({
    'font_size': 10,
    'font_name': 'Tahoma',
    'fg_color': '#fffff0',  # Ivory
    'border': 1,
    'align': 'center',
    'valign': 'vcenter'
})

# ячейки с надписью Итого
summary_sum_format = workbook.add_format({
    'font_size': 11,
    'font_name': 'Tahoma',
    'bold': True,
    'fg_color': '#f08080',
    'border': 2,
    'align': 'center',
})


def write_data(place, data, fmt=sensors_row_data_format, ws=worksheet):
    ws.write(place, data, fmt)


def fill_sensors_data(report):
    ns = len(report.sensors) - 1

    #  Разметка
    ranges_to_merge = [f'A13:A{ns+12}',
                       f'B13:B{ns+12}',
                       f'H13:I{ns+12}',
                       ]
    ranges_to_merge.extend(
        tuple(map(lambda x: f"{x}13:{x}{ns+13}", ['J', 'K', 'L', 'M', 'N'])))
    for rng in ranges_to_merge:
        worksheet.merge_range(rng, rng,
                              sensors_row_data_format)
    worksheet.merge_range(f"A{ns+13}:D{ns+13}", 'Итого:', summary_sum_format)
    # _____Разметка

    #  Запись данных
    write_data('C6', report.object_name, report_text_format)
    write_data(
        'C7', f"С {report.start_date} по {report.end_date}", report_text_format)
    write_data('C8', report.user, report_text_format)
    write_data('C9', 'Моточасы', report_text_format)
    write_data('A13', report.object_name)
    worksheet.write_blank('B13', None, sensors_row_data_format)
    write_data('H13', report.total_fuel_consumption)
    write_data('J13', report.remaining_fuel_start)
    write_data('L13', report.remaining_fuel_end)
    write_data('K13', report.total_refuels)
    write_data('M13', report.engine_hours_km)
    write_data('N13', report.mileage)
    worksheet.write_row(f'E{13+ns}', [report.twh, report.engine_hours, '',
                                      report.fuel_consumption_h, report.fuel_consumption_mh],
                        sensors_row_data_format)

    for (idx, s) in enumerate(report.sensors_data):
        print(f"{idx}, {s}")
        worksheet.write_row(xl_rowcol_to_cell(
            12 + idx, 2), s, sensors_row_data_format)

    #
    return ranges_to_merge


column_width_list = list(map(lambda x: x * 4.1, [2, 2, 4, 2.8, 2.37,
                                                 2.37, 4, 2.6, 2.6, 2.1, 2.1, 2.1, 2.3, 2.1]))

for (idx, wth) in enumerate(column_width_list):
    worksheet.set_column(idx, idx, wth)

fill_sensors_data(reports[0])  # DELETE THIS !!!!!!!!!!!!!!


while True:
    try:
        workbook.close()
    except xlsxwriter.exceptions.FileCreateError as e:
        decision = input("Exception caught in workbook.close(): %s\n"
                         "Please close the file if it is open in Excel.\n"
                         "Try to write file again? [Y/n]: " % e)
        if decision != 'n':
            continue

    break
