# Copyright © 2017 Ondrej Martinsky, All rights reserved
# http://github.com/omartinsky/pybor
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from yc_helpers import *

from datetime import date
from dateutil.relativedelta import relativedelta
from numpy import *
import dateutil.parser

class Tenor:
    def __init__(self, s):
        try:
            self.string = s
            self.n = s[:-1]
            self.n = int(self.n) if self.n != "" else 0
            self.unit = s[-1:]
        except BaseException as ex:
            raise BaseException("Unable to parse tenor %s" % s) from ex

    def __str__(self):
        return self.string

excelBaseDate = date(1899, 12, 30)

def toexceldate(d):
    return int((d - excelBaseDate).days)

def fromexceldate(d):
    assert_type(d, int)
    return excelBaseDate + relativedelta(days=d)

def add_tenor_to_date(date, tenor):
    assert_type(date, int)
    assert_type(tenor, Tenor)
    assert tenor.unit != 'E'
    return toexceldate(fromexceldate(date) + create_relativedelta(tenor.n, tenor.unit))

def create_date(arg, reference_date=None):
    if isinstance(arg, int):
        return arg
    elif isinstance(arg, date):
        return toexceldate(arg)
    elif isinstance(arg, str) and arg[0:4].isdigit():
        return toexceldate(dateutil.parser.parse(arg).date())
    elif isinstance(arg, str):
        assert reference_date is not None
        ret = reference_date
        tenors = arg.split("+")
        for t in tenors:
            if t == 'E': continue
            ret = add_tenor_to_date(ret, Tenor(t))
        return ret
    elif isinstance(arg, Tenor):
        assert reference_date is not None
        return create_date(reference_date, arg)
        if arg.unit == 'E':
            return reference_date
        return add_tenor_to_date(reference_date, arg)
    assert False, (type(arg), arg)


def calculate_dcfs(dates):
    numerator = dates[1:] - dates[:-1]
    return numerator / 365. # TODO


def calculate_dcf(date0, date1, dcc):
    numerator = date1 - date0
    return numerator / dcc.get_denominator()


def date_step(t, n, unit, eom=False):
    assert_type(t, int)
    assert eom == False, "not implemented"
    return toexceldate(fromexceldate(t) + create_relativedelta(n, unit))


def create_relativedelta(n, unit):
    if unit == 'M':
        return relativedelta(months=n)
    elif unit == 'B':
        return relativedelta(days=n)
    elif unit == 'Y':
        return relativedelta(years=n)
    elif unit == 'F':
        return relativedelta(months=3 * n)   # todo
    else:
        raise BaseException("Unknown unit %s" % unit)


def generate_schedule(start, end, step):
    assert_type(start, int)
    assert_type(end, int)
    assert_type(step, Tenor)
    d = start
    out = []
    while d < end:
        out.append(d)
        d = date_step(d, step.n, step.unit)
    out.append(end)
    return array(out)

# endregion
