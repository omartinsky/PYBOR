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

# Example: Fixed GBP vs. Floating USD.LIBOR.3M

class CrossCurrencySwap(Instrument):
    def __init__(self, name, curve_discount_l, curve_discount_r, curve_forecast_r, reference_date, start, length,
                 convention_l, convention_r):
        super().__init__(name)
        assert_type(name, str)
        assert_type(curve_forecast_r, str)
        assert_type(curve_discount_l, str)
        assert_type(curve_discount_r, str)
        assert_type(convention_l, Convention)
        assert_type(convention_r, Convention)
        self.convention_l_ = convention_l
        self.convention_r_ = convention_r
        self.curve_forecast_r_ = curve_forecast_r
        self.curve_discount_l_ = curve_discount_l
        self.curve_discount_r_ = curve_discount_r
        self.start_ = create_date(start, reference_date)
        self.end_ = date_step(self.start_, length)
        self.accruals_l_ = generate_schedule(self.start_, self.end_, self.convention_l_.payment_frequency)
        self.accruals_r_ = generate_schedule(self.start_, self.end_, self.convention_r_.payment_frequency)
        self.dcf_l_ = calculate_dcfs(self.accruals_l_, self.convention_l_.dcc)
        self.dcf_r_ = calculate_dcfs(self.accruals_r_, self.convention_r_.dcc)

    def get_start_date(self):
        return self.start_

    def get_pillar_date(self):
        return self.end_

    def calc_par_rate(self, curvemap):
        fcurve_r = curvemap[self.curve_forecast_r_]
        dcurve_l = curvemap[self.curve_discount_l_]
        dcurve_r = curvemap[self.curve_discount_r_]
        rr = fcurve_r.get_fwd_rate(self.accruals_r_, CouponFreq.ZERO, self.convention_r_.dcc)
        df_l = dcurve_l.get_df(self.accruals_l_)
        df_r = dcurve_r.get_df(self.accruals_r_)
        nominator_r = sum(rr * self.dcf_r_ * df_r[1:])
        notional_r = df_r[0] - df_r[-1]
        notional_l = df_l[0] - df_l[-1]
        denumerator_l = sum(self.dcf_l_ * df_l[1:])
        return (nominator_r - notional_r + notional_l) / denumerator_l
