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


# Example: Floating GBP.LIBOR.3M + spread vs. Floating USD.LIBOR.3M with MTM resets

class MtmCrossCurrencyBasisSwap(Instrument):
    @staticmethod
    def CreateFromDataFrameRow(name, eval_date, row):
        fcastL, fcastR, discL, discR, convL, convR, start, length = get_dataframe_row_cells(row)
        assert_is_set([discL, discR, fcastL, fcastR, convL, convR])
        return MtmCrossCurrencyBasisSwap(name,
                                         curve_discount_l=discL,
                                         curve_discount_r=discR,
                                         curve_forecast_l=fcastL,
                                         curve_forecast_r=fcastR,
                                         trade_date=eval_date,
                                         start=start,
                                         length=Tenor(length),
                                         convention_l=global_conventions.get(convL),
                                         convention_r=global_conventions.get(convR))

    def __init__(self,
                 name: str,
                 curve_discount_l: str,
                 curve_discount_r: str,
                 curve_forecast_l: str,
                 curve_forecast_r: str,
                 trade_date,
                 start,
                 length,
                 convention_l: Convention,
                 convention_r: Convention):
        super().__init__(name)
        self.convention_l_ = convention_l
        self.convention_r_ = convention_r
        self.curve_forecast_l_ = curve_forecast_l
        self.curve_forecast_r_ = curve_forecast_r
        self.curve_discount_l_ = curve_discount_l
        self.curve_discount_r_ = curve_discount_r
        self.start_ = create_date(start, trade_date)
        self.end_ = date_step(self.start_, length)
        self.accruals_l_ = generate_schedule(self.start_, self.end_, self.convention_l_.payment_frequency)
        self.accruals_r_ = generate_schedule(self.start_, self.end_, self.convention_r_.payment_frequency)
        self.dcf_l_ = calculate_dcfs(self.accruals_l_, self.convention_l_.dcc)
        self.dcf_r_ = calculate_dcfs(self.accruals_r_, self.convention_r_.dcc)

    def get_pillar_date(self):
        return self.end_

    def calc_par_rate(self, curvemap):
        fcurve_l = curvemap[self.curve_forecast_l_]
        fcurve_r = curvemap[self.curve_forecast_r_]
        dcurve_l = curvemap[self.curve_discount_l_]
        dcurve_r = curvemap[self.curve_discount_r_]
        rl = fcurve_l.get_fwd_rate_aligned(self.accruals_l_, CouponFreq.ZERO, self.convention_l_.dcc)
        rr = fcurve_r.get_fwd_rate_aligned(self.accruals_r_, CouponFreq.ZERO, self.convention_r_.dcc)
        df_l = dcurve_l.get_df(self.accruals_l_)
        df_r = dcurve_r.get_df(self.accruals_r_)
        dcf_l = self.dcf_l_
        dcf_r = self.dcf_r_

        npv_right = -df_r[0] \
                    + df_r[-1] * df_l[-1] / df_r[-1] \
                    + sum(rr * dcf_r * df_r[1:] * df_l[:-1] / df_r[:-1]) \
                    - sum((df_l[1:] / df_r[1:] - df_l[:-1] / df_r[:-1]) * df_r[1:])

        rate = (npv_right + df_l[0] - df_l[-1] - sum(rl * dcf_l * df_l[1:])) / sum(dcf_l * df_l[1:])
        return rate
