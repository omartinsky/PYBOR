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


# Example: USD.LIBOR.3M vs. USD.LIBOR.6M + spread

class BasisSwap(Instrument):
    @staticmethod
    def CreateFromDataFrameRow(name, eval_date, row):
        fcastL, fcastR, discL, discR, convL, convR, start, length = get_dataframe_row_cells(row)
        assert_is_set([discL, fcastL, fcastR, convL, convR])
        assert_is_not_set([discR])
        return BasisSwap(name,
                         curve_forecast_l=fcastL,
                         curve_forecast_r=fcastR,
                         curve_discount=discL,
                         trade_date=eval_date,
                         start=start,
                         length=Tenor(length),
                         convention_l=global_conventions.get(convL),
                         convention_r=global_conventions.get(convR))

    def __init__(self, name: str,
                 curve_discount: str,
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
        self.curve_discount_ = curve_discount
        self.start_ = create_excel_date(start, trade_date)
        self.end_ = date_step(self.start_, length)
        self.accruals_l_ = generate_schedule(self.start_, self.end_, self.convention_l_.payment_frequency)
        self.accruals_r_ = generate_schedule(self.start_, self.end_, self.convention_r_.payment_frequency)
        self.dcf_l_ = calculate_dcfs(self.accruals_l_, self.convention_l_.dcc)
        self.dcf_r_ = calculate_dcfs(self.accruals_r_, self.convention_r_.dcc)

    def get_pillar_date(self):
        return self.end_

    def calc_par_rate(self, curvemap):
        # Price of instrument is basis which is added to "left" curve
        fcurve_l = curvemap[self.curve_forecast_l_]
        fcurve_r = curvemap[self.curve_forecast_r_]
        dcurve = curvemap[self.curve_discount_]
        rl = fcurve_l.get_fwd_rate_aligned(self.accruals_l_, ZEROFREQ, self.convention_l_.dcc)
        rr = fcurve_r.get_fwd_rate_aligned(self.accruals_r_, ZEROFREQ, self.convention_r_.dcc)
        df_l = dcurve.get_df(self.accruals_l_)
        df_r = dcurve.get_df(self.accruals_r_)
        nominator_l = sum(rl * self.dcf_l_ * df_l[1:])
        nominator_r = sum(rr * self.dcf_r_ * df_r[1:])
        denumerator = sum(self.dcf_l_ * df_l[1:])
        return (nominator_r - nominator_l) / denumerator
