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

from yc_curve import *
from yc_dates import *


class Instrument:
    def __init__(self, name):
        self.name_ = name

    def get_name(self):
        return self.name_

    def get_start_date(self):
        assert False, 'method must be implemented in child class %s' % type(self)

    def get_pillar_date(self):
        assert False, 'method must be implemented in child class %s' % type(self)

    def calc_par_rate(self, curvemap):
        assert False, 'method must be implemented in child class %s' % type(self)

    def drdp(self):
        return 1.e+2

    def price_from_par_rate(self, x): # TODO rename quote_from_rate
        return x*1.e+2

    def par_rate_from_price(self, x): # TODO rename rate_from_quote
        return x*1.e-2

    def __str__(self):
        return self.name_
