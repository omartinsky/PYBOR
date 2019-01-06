# Copyright © 2017 Ondrej Martinsky, All rights reserved
# http://github.com/omartinsky/pybor

from yc_date import *

def is_weekend(date):
    date = exceldate_to_pydate(date)
    dow = date.weekday()
    # 0,1,2,3,4 is Monday to Friday
    # 5,6 is Saturday, Sunday
    return dow >= 5

class CalendarBase:
    def __init__(self):
        pass

    def is_holiday(self, date):
        assert False, 'method must be implemented in child class %s' % type(self)

class WeekendCalendar(CalendarBase):
    def __init__(self):
        super().__init__()

    def is_holiday(self, date):
        assert isinstance(date, int)
        return is_weekend(date)

class EnumeratedCalendar(CalendarBase):
    def __init__(self, holidays):
        assert isinstance(holidays, set)
        assert all([isinstance(x, int) for x in holidays])
        self.holidays_ = holidays

    def get_holidays(self):
        return self.holidays_

    def is_holiday(self, date):
        assert isinstance(date, int)
        return is_weekend(date) or date in self.holidays_

def union_calendars(calendars):
    assert len(calendars) >= 1
    if len(calendars)==1:
        return calendars[0]
    holidays = set()
    for cal in calendars:
        holidays = holidays | cal.get_holidays()
    return EnumeratedCalendar(holidays)

class Calendars:
    def __init__(self):
        #TODO Complete the calendars below
        self.dictionary = {
            'London'  : EnumeratedCalendar(set()),
            'NewYork' : EnumeratedCalendar(set()),
            }

    def get(self, calendar_name):
        assert isinstance(calendar_name, str)
        names = calendar_name.split("+")
        if len(names)==1:
            name = names[0]
            if name not in self.dictionary:
                raise BaseException("Calendar with name %s not found" % name)
            return self.dictionary[name]
        else:
            return union_calendars([self.get(name) for name in names])

global_calendars = Calendars()
