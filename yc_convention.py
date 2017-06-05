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


from yc_dates import *
import enum


class DCC(enum.Enum):
    ACT365 = 0
    ACT360 = 1

    def get_denominator(self):
        if self == DCC.ACT360:
            return 360.
        elif self == DCC.ACT365:
            return 365.
        assert False


class CalculationType(enum.Enum):
    PLAIN = 0
    AVERAGING = 1
    NONE = 2


class CouponFreq(enum.Enum):
    CONTINUOUS = 0
    DAILY = 1
    QUARTERLY = 2
    ZERO = 3


class Convention:
    def __init__(self, payment_frequency, forecast_frequency, calculation_type, dcc):
        assert_type(payment_frequency, Tenor)
        assert_type(forecast_frequency, Tenor)
        assert_type(calculation_type, CalculationType)
        assert_type(dcc, DCC)
        self.payment_frequency = payment_frequency
        self.forecast_frequency = forecast_frequency
        self.calculation_type = calculation_type
        self.dcc = dcc


global_conventions = {
    'USDLIBOR3M':             Convention(Tenor("3M"), Tenor("3M"), CalculationType.PLAIN, DCC.ACT360),
    'USDLIBOR6M':             Convention(Tenor("6M"), Tenor("6M"), CalculationType.PLAIN, DCC.ACT360),
    'USDLIBOR12M':            Convention(Tenor("12M"), Tenor("12M"), CalculationType.PLAIN, DCC.ACT360),
    'USDOIS':                 Convention(Tenor("3M"), Tenor("1B"), CalculationType.AVERAGING, DCC.ACT360),
    'USD-USDOIS':             Convention(Tenor("3M"), Tenor("1B"), CalculationType.NONE, DCC.ACT360),
    'GBP-USDOIS':             Convention(Tenor("3M"), Tenor("1B"), CalculationType.NONE, DCC.ACT365),
    'GBP-GBPSONIA':           Convention(Tenor("3M"), Tenor("1B"), CalculationType.NONE, DCC.ACT365),
    'GBPLIBOR3M':             Convention(Tenor("3M"), Tenor("3M"), CalculationType.PLAIN, DCC.ACT365),
}

