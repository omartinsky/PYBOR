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

from instruments.base_instrument import *

class Future(Instrument):
    def __init__(self, name, curve_forecast, start, len):
        super().__init__(name)
        assert_type(name, str)
        assert_type(curve_forecast, str)
        self.curve_forecast = curve_forecast
        self.start_ = start
        self.end_ = date_step(self.start_, len.n, len.unit)
        self.accruals_ = array([self.start_, self.end_])
        self.dcf_ = calculate_dcfs(self.accruals_)[0]

    def get_start_date(self):
        return self.start_

    def get_pillar_date(self):
        return self.end_

    def calc_par_rate(self, curvemap):
        curve = curvemap[self.curve_forecast]
        df = curve.get_df(self.accruals_)
        return (df[0] / df[1] - 1) / self.dcf_

    def drdp(self):
        return -100

    def price_from_rate(self,x):
        return 100 - (x * 1.e+2)

    def rate_from_price(self,x):
        return (100 - x) * 1.e-2
