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
    @staticmethod
    def CreateFromDataFrameRow(name, eval_date, row):
        fcastL, fcastR, discL, discR, convL, convR, start, length = get_dataframe_row_cells(row)
        assert_is_set([discL, fcastL, convL])
        assert_is_not_set([discR, fcastR, convR])
        return TermDeposit(name,
                           curve_forecast=fcastL,
                           curve_discount=discL,
                           trade_date=eval_date,
                           start=start,
                           length=Tenor(length),
                           convention=global_conventions.get(convL))

    def __init__(self,
                 name: str,
                 curve_forecast: str,
                 curve_discount: str,
                 trade_date: int,
                 start,
                 length: Tenor,
                 convention: Convention):
        super().__init__(name)
        self.convention_ = convention
        self.curve_forecast_ = curve_forecast
        self.curve_discount_ = curve_discount
        self.start_ = create_date(start, trade_date)
        self.end_ = date_step(self.start_, length)
        self.accruals_ = generate_schedule(self.start_, self.end_, self.convention_.payment_frequency)
        self.dcf_ = calculate_dcfs(self.accruals_, convention.dcc)

    def get_pillar_date(self):
        return self.end_

    def calc_par_rate(self, curvemap):
        fcurve = curvemap[self.curve_forecast_]
        dcurve = curvemap[self.curve_discount_]
        r = fcurve.get_fwd_rate_aligned(self.accruals_, CouponFreq.ZERO, self.convention_.dcc)
        df = dcurve.get_df(self.accruals_)
        nominator = sum(r * self.dcf_ * df[1:])
        denumerator = sum(self.dcf_ * df[1:])
        df_s = df[0]
        df_e = df[-1]
        price = (df_s - df_e - nominator) / denumerator
        return price
