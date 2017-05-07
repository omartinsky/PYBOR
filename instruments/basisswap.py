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


class BasisSwap(Instrument):
    def __init__(self, name, curve_forecast_l, curve_forecast_r, curve_discount, start, length, convention_l,
                 convention_r):
        super().__init__(name)
        assert_type(name, str)
        assert_type(curve_forecast_l, str)
        assert_type(curve_forecast_r, str)
        assert_type(curve_discount, str)
        assert_type(convention_l, Convention)
        assert_type(convention_r, Convention)
        self.convention_l_ = convention_l
        self.convention_r_ = convention_r
        self.curve_forecast_l_ = curve_forecast_l
        self.curve_forecast_r_ = curve_forecast_r
        self.curve_discount_ = curve_discount
        self.start_ = start
        self.end_ = date_step(self.start_, length.n, length.unit)
        self.accruals_l_ = generate_schedule(self.start_, self.end_, self.convention_l_.payment_frequency)
        self.accruals_r_ = generate_schedule(self.start_, self.end_, self.convention_r_.payment_frequency)
        self.dcf_l_ = calculate_dcfs(self.accruals_l_)
        self.dcf_r_ = calculate_dcfs(self.accruals_r_)

    def get_start_date(self):
        return self.start_

    def get_pillar_date(self):
        return self.end_

    def calc_par_rate(self, curvemap):
        # Price of instrument is basis which is added to "left" curve
        fcurve_l = curvemap[self.curve_forecast_l_]
        fcurve_r = curvemap[self.curve_forecast_r_]
        dcurve = curvemap[self.curve_discount_]
        rl = fcurve_l.get_rate(self.accruals_l_, CouponFreq.ZERO, self.convention_l_.dcc)
        rr = fcurve_r.get_rate(self.accruals_r_, CouponFreq.ZERO, self.convention_r_.dcc)
        df_l = dcurve.get_df(self.accruals_l_)
        df_r = dcurve.get_df(self.accruals_r_)
        nominator_l = sum(rl * self.dcf_l_ * df_l[1:])
        nominator_r = sum(rr * self.dcf_r_ * df_r[1:])
        denumerator = sum(self.dcf_l_ * df_l[1:])
        return (nominator_r - nominator_l) / denumerator
