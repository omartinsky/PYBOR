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


from yc_convention import *
import scipy.interpolate
import pylab, re, collections

class CurveMap(collections.OrderedDict):
    def __init__(self, *arg, **kw):
        super(CurveMap, self).__init__(*arg, **kw)

    def add_curve(self, c):
        assert_type(c, Curve)
        self[c.get_id()] = c

    def get_all_dofs(self):
        dofs = list()
        for k, v in self.items():
            dofs.extend(v.get_all_dofs())
        return dofs

    def set_all_dofs(self, dofs):
        i = 0
        for k, v in self.items():
            j = i + v.get_dofs_count()
            v.set_all_dofs(dofs[i:j])
            i = j

    def plot(self, reg=".*"):
        for name, curve in sorted(self.items()):
            if re.match(reg, name):
                curve.plot()


class InterpolationMode(enum.Enum):
    LINEAR_LOGDF = 0
    LINEAR_CCZR = 1
    CUBIC_LOGDF = 2


class Curve:
    def __init__(self, curve_id, eval_date, times, dfs, interpolation_mode):
        try:
            times, dfs = array(times), array(dfs)
            assert_type(interpolation_mode, InterpolationMode)
            assert len(times) > 0, "Vector of times is empty"
            assert times[0] != eval, "DF at eval date cannot be provided externally. It is assumed to be 1.0 always"
            self.id_ = curve_id
            self.times_ = append(eval_date, times)
            self.dfs_ = append([1.], dfs)
            self.set_interpolator(interpolation_mode)
        except BaseException as ex:
            raise BaseException("Unable to create curve %s" % curve_id) from ex

    def add_another_curve(self, another_curve):
        assert isinstance(another_curve, Curve)
        assert all(self.times_ == another_curve.times_)
        self.dfs_ = another_curve.dfs_ * self.dfs_
        self.set_interpolator(self.interpolation_mode_)

    def set_interpolator(self, interpolation_mode=None):
        if interpolation_mode is not None:
            self.interpolation_mode_ = interpolation_mode
        if self.interpolation_mode_ in [InterpolationMode.LINEAR_LOGDF, InterpolationMode.LINEAR_CCZR]:
            kind = 'linear'
        elif self.interpolation_mode_ in [InterpolationMode.CUBIC_LOGDF]:
            kind = 'cubic'
        else:
            raise BaseException("Invalid interpolation mode. Allowed modes are %s" % enum_values_as_string(InterpolationMode))
        #
        assert len(self.times_) == len(self.dfs_), (len(self.times_), len(self.dfs_))
        #
        if self.interpolation_mode_ in [InterpolationMode.LINEAR_LOGDF, InterpolationMode.CUBIC_LOGDF]:
            logdf = log(self.dfs_)
            interp = scipy.interpolate.interp1d(self.times_, logdf, kind=kind)
            self.interpolator_ = lambda t: exp(interp(t))
        elif self.interpolation_mode_ in [InterpolationMode.LINEAR_CCZR]:
            t_eval = self.get_eval_date()
            t_rel = self.times_-t_eval
            if self.times_[0] == t_eval:
                cczr1 = log(self.dfs_[1:]) / t_rel[1:]
                cczr = insert(cczr1, 0, cczr1[1]) # ZZCR at t0 is undefined, take it from t1 instead
            else:
                cczr = log(self.dfs_) / t_rel

            interp = scipy.interpolate.interp1d(self.times_, cczr, kind=kind)
            self.interpolator_ = lambda t: exp(interp(t) * (t - t_eval))
        else:
            raise BaseException("Invalid interpolation mode")

    def __str__(self):
        return self.id_

    def get_eval_date(self):
        return self.times_[0]

    def get_id(self):
        return self.id_

    def get_df(self, t):
        return self.interpolator_(t)

    def get_rate(self, t, freq, dcc):
        dfs = self.get_df(t)
        t1 = t[:-1]
        t2 = t[1:]
        df1 = dfs[:-1]
        df2 = dfs[1:]
        dcf = calculate_dcf(t1, t2, dcc)
        if freq == CouponFreq.ZERO:
            return (df1 / df2 - 1) / dcf
        if freq == CouponFreq.CONTINUOUS:
            return -log(df2 / df1) / dcf

    def set_all_dofs(self, dofs):
        self.dfs_ = append([1], dofs)
        self.set_interpolator()

    def get_all_dofs(self):
        return self.dfs_[1:]

    def get_dofs_count(self):
        return len(self.dfs_) - 1

    def plot_df(self, samples=1000):
        X, Y = [], []
        timesample = linspace(0, self.times_[-1], samples)
        X = timesample
        Y = self.get_df(timesample)
        pylab.plot(X, Y, label=self.id_)

    def plot(self, samples=1000):
        X, Y = [], []
        timesample = linspace(0, self.times_[-1], samples)
        X = timesample[:-1]
        conv = conventions[self.id_]
        Y = self.get_rate(timesample, CouponFreq.CONTINUOUS, conv.dcc)
        pylab.plot(X, Y, label=self.id_)

class CurveConstructor:
    @staticmethod
    def FromShortRateModel(curve_id, times, r0, speed, mean, sigma, interpolation):
        import random
        times = array(times)
        assert_type(r0, float)
        assert_type(speed, float)
        assert_type(mean, float)
        assert_type(sigma, float)
        assert_type(interpolation, InterpolationMode)
        r = r0
        rates = []
        dts = times[1:] - times[:-1]
        dts = dts / 365.
        for dt in dts:
            rates.append(r)
            dr = speed * (mean - r) * dt + sigma * random.gauss(0, 1) * dt ** .5
            r += dr
        rates = array(rates)
        dfs_fwd = exp(-rates * dts)
        dfs = cumprod(dfs_fwd)
        return Curve(curve_id, times[0], times[1:], dfs, interpolation)
