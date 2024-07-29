import re

from datetime import datetime, timedelta


def seconds_to_str(seconds: int, seconds_needed: bool = False) -> str:
    """
    :return Возвращает время в формате 00:00(:00) из секунд
    """

    mm, ss = divmod(seconds, 60)
    hh, mm = divmod(mm, 60)

    if seconds_needed:
        s = '%02d:%02d:%02d' % (hh, mm, ss)
    else:
        s = '%02d:%02d' % (hh, mm)

    return s


def seconds_to_simple_time_str(seconds: int, hours_needed: bool = True, seconds_needed: bool = False) -> str:
    """
    :return Возвращает время в формате 00ч 00м (00с) из секунд
    """

    mm, ss = divmod(seconds, 60)
    hh, mm = divmod(mm, 60)

    s = ''

    if hours_needed:
        s += '%02dч ' % (hh)
    else:
        mm += hh * 60

    s += '%02dм' % (mm)

    if seconds_needed:
        s += ' %02dс' % (ss)

    return s


def is_correct_person_name(name: str, middlename_needed: bool = True):
    """
    Проверяет корректность ФИО человека
    
    :return False в случае некорректного ФИО, list[str] из фамилии, имени и отчества в случае корректности
    """

    name_splited = name.strip().split(' ', 2 if middlename_needed else 1)
    
    if len(name_splited) < 2:
        return False
    elif len(name_splited) < 3 and middlename_needed:
        name_splited.append('')
    
    return name_splited



def snils_to_str(snils: int) -> str:
    snils = str(snils)
    return snils[:3] + '-' + snils[3:6] + '-' + snils[6:9] + ' ' + snils[9:]


def check_date_format(date_string):
    pattern = r"^\d{2}\.\d{2}$"
    if re.match(pattern, date_string):
        return True
    return False


def parse_time_range(time_range_str):
    """
    Проверка строки диапазона времени в формате «10:00–20:00».

    Возвращает False, если при вводе допущена ошибка.
    """
    pattern = r"^(\d{1,2}):(\d{2}) ?-? ?(\d{1,2}):(\d{2})$"
    match = re.match(pattern, time_range_str)
    if match:
        hour1, min1, hour2, min2 = [int(x) for x in match.groups()]
        if hour1 > hour2 or (hour1 == hour2 and min1 >= min2):
            return False
        return [hour1, min1, hour2, min2]
    else:
        return False


def get_week_date(period):
    today = datetime.today().date()
    monday = today - timedelta(days=today.weekday())
    if period == "Текущая неделя":
        str = monday.strftime('%d.%m.%Y')
        return datetime.strptime(str, '%d.%m.%Y')
    elif period == "Следующая неделя":
        next_monday = monday + timedelta(days=7)
        str = next_monday.strftime('%d.%m.%Y')
        return datetime.strptime(str, '%d.%m.%Y')
    
    elif period == "Сегодня": 
        str = today.strftime('%d.%m.%Y')
        return datetime.strptime(str, '%d.%m.%Y')
    elif period == "Завтра": 
        tomorrow = today + timedelta(days=1)
        str = tomorrow.strftime('%d.%m.%Y')
        return datetime.strptime(str, '%d.%m.%Y')
    elif period == "Вчера":
        yesterday = today - timedelta(days=1)
        str = yesterday.strftime('%d.%m.%Y')
        return datetime.strptime(str, '%d.%m.%Y')
    else:
        raise ValueError("Invalid period")


def phone_number_to_str(phone_number: int) -> str:
    phone_number_str = str(phone_number)
    return f'{"" if phone_number_str[0] == "8" else "+"}{phone_number_str[:-10]} ({phone_number_str[-10:-7]}) {phone_number_str[-7:-4]}-{phone_number_str[-4:-2]}-{phone_number_str[-2:]}'
