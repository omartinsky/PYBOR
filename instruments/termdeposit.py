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

class TermDeposit(Instrument):
    def __init__(self, name, curve_forecast, curve_discount, reference_date, start, length, convention):
        super().__init__(name)
        assert_type(name, str)
        assert_type(curve_forecast, str)
        assert_type(curve_discount, str)
        assert_type(convention, Convention)
        assert_type(reference_date, int)
        self.convention_ = convention
        self.curve_forecast_ = curve_forecast
        self.curve_discount_ = curve_discount
        self.start_ = create_date(start, reference_date)
        self.end_ = date_step(self.start_, length)
        self.accruals_ = generate_schedule(self.start_, self.end_, self.convention_.payment_frequency)
        self.dcf_ = calculate_dcfs(self.accruals_, convention.dcc)

    def get_start_date(self):
        return self.start_

    def get_pillar_date(self):
        return self.end_

    def calc_par_rate(self, curvemap):
        fcurve = curvemap[self.curve_forecast_]
        dcurve = curvemap[self.curve_discount_]
        r = fcurve.get_fwd_rate(self.accruals_, CouponFreq.ZERO, self.convention_.dcc)
        df = dcurve.get_df(self.accruals_)
        nominator = sum(r * self.dcf_ * df[1:])
        denumerator = sum(self.dcf_ * df[1:])
        df_s = df[0]
        df_e = df[-1]
        price = (df_s - df_e - nominator) / denumerator
        return price

