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

# Example: Fixed USD vs. Floating USD.LIBOR.3M

class Swap(Instrument):
    @staticmethod
    def CreateFromDataFrameRow(name, eval_date, row):
        fcastL, fcastR, discL, discR, convL, convR, start, length = get_dataframe_row_cells(row)
        assert_is_set([discL, fcastL, convL, convR])
        assert_is_not_set([discR, fcastR])
        return Swap(name,
                    curve_forecast=fcastL,
                    curve_discount=discL,
                    trade_date=eval_date,
                    start=start,
                    length=Tenor(length),
                    convention_fixed=global_conventions.get(convL),
                    convention_float=global_conventions.get(convR))

    def __init__(self, name, curve_forecast, curve_discount, trade_date, start, length, convention_fixed, convention_float):
        super().__init__(name)
        assert_type(name, str)
        assert_type(curve_forecast, str)
        assert_type(curve_discount, str)
        assert_type(convention_fixed, Convention)
        assert_type(convention_float, Convention)
        self.convention_fixed_ = convention_fixed
        self.convention_float_ = convention_float
        self.curve_forecast_ = curve_forecast
        self.curve_discount_ = curve_discount
        self.start_ = create_date(start, trade_date)
        self.end_ = date_step(self.start_, length)
        self.accruals_fixed_ = generate_schedule(self.start_, self.end_, self.convention_fixed_.payment_frequency)
        self.accruals_float_ = generate_schedule(self.start_, self.end_, self.convention_float_.payment_frequency)
        self.dcf_fixed_ = calculate_dcfs(self.accruals_fixed_, self.convention_fixed_.dcc)
        self.dcf_float_ = calculate_dcfs(self.accruals_float_, self.convention_float_.dcc)

    def get_pillar_date(self):
        return self.end_

    def calc_par_rate(self, curvemap):
        fcurve = curvemap[self.curve_forecast_]
        dcurve = curvemap[self.curve_discount_]
        r = fcurve.get_fwd_rate_aligned(self.accruals_float_, CouponFreq.ZERO, self.convention_float_.dcc)
        df = dcurve.get_df(self.accruals_fixed_)
        nominator = sum(r * self.dcf_float_ * df[1:])
        denumerator = sum(self.dcf_fixed_ * df[1:])
        return nominator / denumerator
