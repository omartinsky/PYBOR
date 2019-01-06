# Copyright © 2017 Ondrej Martinsky, All rights reserved
# http://github.com/omartinsky/pybor

from yc_convention import *
import scipy.interpolate
import pylab, re, collections, matplotlib

class PlottingHelper:
    @staticmethod
    def set_tenors_on_axis(axis, start_date):
        tenors = "6M,1Y,2Y,3Y,4Y,5Y,7Y,10Y,15Y,20Y,30Y,40Y,50Y,60Y,70Y".split(",")
        tenordates = [date_step(int(start_date), Tenor(t)) for t in tenors]
        axis.xaxis.set_ticks(tenordates)
        axis.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, pos: tenors[pos]))

class CurveMap:
    def __init__(self, *arg, **kw):
        super(CurveMap, self).__init__(*arg, **kw)
        self.curves_ = collections.OrderedDict()

    def add_curve(self, c):
        assert_type(c, Curve)
        self.curves_[c.get_id()] = c

    def get_all_dofs(self, curves_for_stage):
        dofs = list()
        for k, v in self.curves_.items():
            if k in curves_for_stage:
                dofs.extend(v.get_all_dofs())
        return dofs

    def set_all_dofs(self, curves_for_stage, dofs):
        i = 0
        for k, v in self.curves_.items():
            if k in curves_for_stage:
                j = i + v.get_dofs_count()
                v.set_all_dofs(dofs[i:j])
                i = j

    def __getitem__(self, item):
        return self.curves_[item]

    def __len__(self):
        return len(self.curves_)

    def keys(self):
        return self.curves_.keys()

    def plot(self, reg=".*", *arg, **kwargs):
        for name, curve in sorted(self.curves_.items()):
            if re.match(reg, name):
                curve.plot(*arg, **kwargs)


class InterpolationMode(enum.Enum):
    LINEAR_LOGDF = 0
    LINEAR_CCZR = 1
    CUBIC_LOGDF = 2

class PlotMode(enum.Enum):
    DF = 0
    ZR = 1
    FWD = 2

class PlotDate(enum.Enum):
    YMD = 0
    EXCEL = 1
    TENOR = 2

class ExponentialInterpolator:
    def __init__(self, interp):
        self.interp = interp
    def value(self, t):
        return exp(self.interp(t))

class ZeroRateInterpolator:
    def __init__(self, interp, t_eval):
        self.interp = interp
        self.t_eval = t_eval
    def value(self, t):
        return exp(self.interp(t) * (t - self.t_eval))

class Curve:
    def __init__(self, curve_id, eval_date, times, dfs, interpolation_mode):
        try:
            times, dfs = array(times), array(dfs)
            assert_type(interpolation_mode, InterpolationMode)
            assert len(times) > 0, "Vector of times is empty"
            assert times[0] != eval_date, "DF at eval date cannot be provided externally. It is assumed to be 1.0 always."
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
            self.interpolator_ = ExponentialInterpolator(interp)
        elif self.interpolation_mode_ in [InterpolationMode.LINEAR_CCZR]:
            t_eval = self.times_[0]
            t_rel = self.times_-t_eval
            cczr1 = log(self.dfs_[1:]) / t_rel[1:]
            cczr = insert(cczr1, 0, cczr1[0]) # ZZCR at t0 is undefined, take it from t1 instead
            interp = scipy.interpolate.interp1d(self.times_, cczr, kind=kind)
            self.interpolator_ = ZeroRateInterpolator(interp, t_eval)
        else:
            raise BaseException("Invalid interpolation mode")

    def __str__(self):
        return self.id_

    def get_id(self):
        return self.id_

    def get_df(self, t):
        try:
            return self.interpolator_.value(t)
        except BaseException as ex:
            raise BaseException("Unable to get discount factor for dates [%i..%i] from curve with dates range [%i..%i]" % (t[0],t[-1],self.times_[0], self.times_[-1])) from ex

    def get_zero_rate(self, t, freq, dcc):
        dfs = self.get_df(t)
        dcf = calculate_dcf(self.times_[0], t, dcc)
        if freq == CouponFreq.ZERO:
            return (1. / dfs - 1.) / dcf
        if freq == CouponFreq.CONTINUOUS:
            return -log(dfs) / dcf

    def get_fwd_rate(self, t_start, t_end, freq, dcc):
        dfs_start = self.get_df(t_start)
        dfs_end = self.get_df(t_end)
        dcf = calculate_dcf(t_start, t_end, dcc)
        if freq == CouponFreq.ZERO:
            return (dfs_start / dfs_end - 1) / dcf
        if freq == CouponFreq.CONTINUOUS:
            return log(dfs_start / dfs_end) / dcf

    def get_fwd_rate_aligned(self, t, freq, dcc):
        # Slightly faster version which relies on the fact that calculation periods are aligned (no overlaps, no gaps)
        dfs = self.get_df(t)
        t1 = t[:-1]
        t2 = t[1:]
        df1 = dfs[:-1]
        df2 = dfs[1:]
        dcf = calculate_dcf(t1, t2, dcc)
        if freq == CouponFreq.ZERO:
            return (df1 / df2 - 1) / dcf
        if freq == CouponFreq.CONTINUOUS:
            return log(df1 / df2) / dcf

    def set_all_dofs(self, dofs):
        self.dfs_ = append([1], dofs)
        self.set_interpolator()

    def get_all_dofs(self):
        return self.dfs_[1:]

    def get_dofs_count(self):
        return len(self.dfs_) - 1

    def plot(self, date_style=PlotDate.YMD, mode=PlotMode.FWD, samples=1000, label=None, convention=None):
        timesample = linspace(self.times_[0], self.times_[-1], samples)
        X = timesample
        if date_style==PlotDate.YMD:
            X = [exceldate_to_pydate(int(x)) for x in X]
        elif date_style==PlotDate.TENOR:
            ax = matplotlib.pyplot.subplot()
            PlottingHelper.set_tenors_on_axis(ax, self.times_[0])
        elif date_style==PlotDate.EXCEL:
            pass
        else:
            raise BaseException("Unknown PlottingDateStyle")
        ###
        if mode==PlotMode.FWD:
            convention = global_conventions.get(self.id_) if convention is None else convention
            Y = self.get_fwd_rate_aligned(timesample, CouponFreq.ZERO, convention.dcc)
            pylab.plot(X[:-1], Y, label=self.id_ if label is None else label)
        elif mode==PlotMode.ZR:
            convention = global_conventions.get(self.id_) if convention is None else convention
            Y = self.get_zero_rate(timesample[1:], CouponFreq.ZERO, convention.dcc)
            pylab.plot(X[:-1], Y, label=self.id_ if label is None else label)
        elif mode==PlotMode.DF:
            Y = self.get_df(timesample)
            pylab.plot(X, Y, label=self.id_ if label is None else label)
        else:
            raise BaseException("Unknown PlottingMode")

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
