# Utils class
import re
from datetime import datetime, timedelta, timezone


class Utils:
    @classmethod
    def now(cls) -> datetime:
        return datetime.now(tz=timezone(offset=timedelta(hours=3)))

    @classmethod
    def now_from_str(
        cls, format: str = '%d.%m.%Y %H:%M:%S',
        day: bool = True, month: bool = True, year: bool = True,
        hour: bool = True, minute: bool = True, second: bool = True, microsecond: bool = False,
        date_sep: str = '.', time_sep: str = ':', middle_sep: str = ' '
    ) -> str:
        datetime_now = cls.now()
        
        datetime_placeholders_values = {
            '%d': datetime_now.day if day else '',
            '%m': datetime_now.month if month else '',
            '%Y': datetime_now.year if year else '',
            '%H': datetime_now.hour if hour else '',
            '%M': datetime_now.minute if minute else '',
            '%S': datetime_now.second if second else '',
            '%f': datetime_now.microsecond if microsecond else ''
        }

        datetime_now_str = ''

        # if day:

    @classmethod
    def timedelta_to_str(cls, delta: timedelta, seconds_needed: bool = False) -> str:
        """
        :return Возвращает время в формате 00:00(:00) из секунд
        """
        seconds = delta.seconds()

        mm, ss = divmod(seconds, 60)
        hh, mm = divmod(mm, 60)

        if seconds_needed:
            s = '%02d:%02d:%02d' % (hh, mm, ss)
        else:
            s = '%02d:%02d' % (hh, mm)

        return s

    @classmethod
    def timedelta_to_simple_time_str(cls, delta: timedelta, hours_needed: bool = True, seconds_needed: bool = False) -> str:
        """
        :return Возвращает время в формате 00ч 00м (00с) из секунд
        """
        seconds = delta.seconds()

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