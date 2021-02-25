# Copyright © 2017 Ondrej Martinsky, All rights reserved
# http://github.com/omartinsky/pybor

import unittest
from teamcity import is_running_under_teamcity
from teamcity.unittestpy import TeamcityTestRunner

from yc_framework import *
from yc_convention import *
from yc_calendar import *

import numpy, random

aae = numpy.testing.assert_almost_equal


def arr(*args) -> np.array:
    return np.array(args)


def dte(arg, reference_date=None):
    return create_excel_date(arg, reference_date)


class EnumTests(unittest.TestCase):
    def test_enum_from_string(self):
        class TestEnum(enum.Enum):
            A = 0
            B = 1

        self.assertEqual(enum_from_string(TestEnum, "A"), TestEnum.A)
        self.assertRaises(BaseException, enum_from_string, TestEnum, "C")


class DateTests(unittest.TestCase):
    def test_tenor(self):
        t = Tenor("3M")
        t2 = -t
        t3 = -t2
        self.assertEqual(t.n, 3)
        self.assertEqual(t.unit, 'M')
        self.assertEqual(t2.n, -3)
        self.assertEqual(t.unit, 'M')
        self.assertEqual(t, t3)

    def test_date_conversion(self):
        from datetime import date
        # Do not test dates before 1900/03/01, because excel incorrectly assumes 1900 is a leap year
        p = date(1900, 3, 1)
        d = pydate_to_exceldate(p)
        self.assertEqual(d, 61)
        self.assertEqual(exceldate_to_pydate(d), date(1900, 3, 1))

    def test_date_creation(self):
        self.assertEqual(dte(43000), 43000)
        self.assertEqual(dte('E', 43000), 43000)
        self.assertEqual(dte('E', dte('20170922')), 43000)
        self.assertEqual(dte('1M', 43000), 43030)
        self.assertEqual(dte(Tenor('1M'), 43000), 43030)
        self.assertEqual(dte('E+1M', 43000), 43030)
        self.assertEqual(dte('E+E+1Y+1M', 43000), 43395)
        self.assertEqual(dte('1970-01-03'), 25571)
        self.assertEqual(dte('1970/01/03'), 25571)
        self.assertEqual(dte('19700103'), 25571)

    def test_dcc(self):
        ACT360 = DCC.ACT360
        ACT365 = DCC.ACT365
        self.assertEqual(calculate_dcf(dte('1995-01-01'), dte('1996-01-01'), ACT365), 1)
        self.assertEqual(calculate_dcf(dte('1996-01-01'), dte('1997-01-01'), ACT365), 366 / 365)
        self.assertEqual(calculate_dcf(dte('1996-01-01'), dte('1997-01-01'), ACT360), 366 / 360)

    def test_generate_schedule(self):
        exceptionLambda = lambda: generate_schedule(dte('1996-01-01'), dte('1997-01-03'), Tenor("3M"),
                                                    STUB_NOT_ALLOWED)
        self.assertRaises(BaseException, exceptionLambda)

        schedule0 = generate_schedule(dte('1996-01-01'), dte('1997-01-01'), Tenor("3M"),
                                      STUB_NOT_ALLOWED)
        schedule1 = generate_schedule(dte('1996-01-01'), dte('1997-01-01'), Tenor("3M"),
                                      BACK_STUB_SHORT)
        schedule2 = generate_schedule(dte('1996-01-01'), dte('1997-01-01'), Tenor("3M"),
                                      BACK_STUB_LONG)
        schedule3 = generate_schedule(dte('1996-01-01'), dte('1997-01-01'), Tenor("3M"),
                                      FRONT_STUB_SHORT)
        schedule4 = generate_schedule(dte('1996-01-01'), dte('1997-01-01'), Tenor("3M"),
                                      FRONT_STUB_LONG)
        self.assertListEqual(list(schedule0), [35065, 35156, 35247, 35339, 35431])
        self.assertListEqual(list(schedule1), [35065, 35156, 35247, 35339, 35431])
        self.assertListEqual(list(schedule2), [35065, 35156, 35247, 35339, 35431])
        self.assertListEqual(list(schedule3), [35065, 35156, 35247, 35339, 35431])
        self.assertListEqual(list(schedule4), [35065, 35156, 35247, 35339, 35431])

        stub_type = BACK_STUB_SHORT
        schedule = generate_schedule(dte('1996-01-01'), dte('1996-12-20'), Tenor("3M"), stub_type)
        self.assertEqual(type(schedule), numpy.ndarray)
        self.assertListEqual(list(schedule), [35065, 35156, 35247, 35339, 35419])

        stub_type = BACK_STUB_LONG
        schedule = generate_schedule(dte('1996-01-01'), dte('1996-12-20'), Tenor("3M"), stub_type)
        self.assertListEqual(list(schedule), [35065, 35156, 35247, 35419])

        stub_type = FRONT_STUB_SHORT
        schedule = generate_schedule(dte('1996-01-20'), dte('1997-01-01'), Tenor("3M"), stub_type)
        self.assertListEqual(list(schedule), [35084, 35156, 35247, 35339, 35431])

        stub_type = FRONT_STUB_LONG
        schedule = generate_schedule(dte('1996-01-20'), dte('1997-01-01'), Tenor("3M"), stub_type)
        self.assertListEqual(list(schedule), [35084, 35247, 35339, 35431])

    def test_tenor(self):
        t = Tenor("-3M")
        self.assertEqual(t.unit, 'M')
        self.assertEqual(t.n, -3)
        self.assertEqual(Tenor('3M'), Tenor('3M'))
        self.assertNotEqual(Tenor('12M'), Tenor('1Y'))

    def test_imm_date(self):
        from datetime import date
        assert next_imm_date(date(2017, 1, 1)) == date(2017, 3, 15)
        assert next_imm_date(date(2017, 3, 1)) == date(2017, 3, 15)
        assert next_imm_date(date(2017, 3, 14)) == date(2017, 3, 15)
        assert next_imm_date(date(2017, 3, 15)) == date(2017, 6, 21)
        assert next_imm_date(date(2017, 6, 20)) == date(2017, 6, 21)
        assert next_imm_date(date(2017, 6, 21)) == date(2017, 9, 20)
        assert next_imm_date(date(2017, 6, 22)) == date(2017, 9, 20)
        assert next_imm_date(date(2017, 9, 19)) == date(2017, 9, 20)
        assert next_imm_date(date(2017, 9, 20)) == date(2017, 12, 20)
        assert next_imm_date(date(2017, 12, 20)) == date(2018, 3, 21)

    def test_date_step(self):
        from datetime import date
        self.assertEqual(date_step(dte(date(2017, 2, 10)), Tenor('3M')), dte(date(2017, 5, 10)))
        self.assertEqual(date_step(dte(date(2017, 2, 10)), Tenor('1Y')), dte(date(2018, 2, 10)))
        self.assertEqual(date_step(dte(date(2017, 2, 10)), Tenor('-1Y')), dte(date(2016, 2, 10)))
        self.assertEqual(date_step(dte(date(2017, 3, 31)), Tenor('1M')), dte(date(2017, 4, 30)))
        self.assertEqual(date_step(dte(date(2017, 2, 10)), Tenor('-1Y'), preserve_eom=True),
                         dte(date(2016, 2, 10)))
        self.assertEqual(date_step(dte(date(2017, 2, 28)), Tenor('-1Y'), preserve_eom=True),
                         dte(date(2016, 2, 29)))
        self.assertEqual(date_step(dte(date(2017, 2, 28)), Tenor('1M'), preserve_eom=True),
                         dte(date(2017, 3, 31)))
        self.assertEqual(date_step(dte(date(2017, 3, 31)), Tenor('1M'), preserve_eom=True),
                         dte(date(2017, 4, 30)))
        self.assertEqual(date_step(dte(date(2017, 2, 28)), Tenor('1D'), preserve_eom=True),
                         dte(date(2017, 3, 31)))
        self.assertEqual(date_step(dte(date(2017, 3, 14)), Tenor('1F')), dte(date(2017, 3, 15)))
        self.assertEqual(date_step(dte(date(2017, 3, 14)), Tenor('2F')), dte(date(2017, 6, 21)))
        self.assertEqual(date_step(dte(date(2017, 3, 15)), Tenor('1F')), dte(date(2017, 6, 21)))
        self.assertEqual(date_step(dte(date(2017, 3, 15)), Tenor('2F')), dte(date(2017, 9, 20)))

    def test_date_roll(self):
        from datetime import date

        F = RollType.FOLLOWING
        P = RollType.PRECEDING
        wc = WeekendCalendar()
        self.assertEqual(date_roll(dte(date(2017, 2, 17)), F, wc), dte(date(2017, 2, 17)))
        self.assertEqual(date_roll(dte(date(2017, 2, 18)), F, wc), dte(date(2017, 2, 20)))
        self.assertEqual(date_roll(dte(date(2017, 2, 19)), F, wc), dte(date(2017, 2, 20)))
        self.assertEqual(date_roll(dte(date(2017, 2, 20)), F, wc), dte(date(2017, 2, 20)))

        self.assertEqual(date_roll(dte(date(2017, 2, 17)), P, wc), dte(date(2017, 2, 17)))
        self.assertEqual(date_roll(dte(date(2017, 2, 18)), P, wc), dte(date(2017, 2, 17)))
        self.assertEqual(date_roll(dte(date(2017, 2, 19)), P, wc), dte(date(2017, 2, 17)))
        self.assertEqual(date_roll(dte(date(2017, 2, 20)), P, wc), dte(date(2017, 2, 20)))

    def test_create_spot_date(self):
        from datetime import date
        d = dte(date(2017, 1, 12))  # Thursday
        d2 = calculate_spot_date(d, 3, WeekendCalendar())
        self.assertEqual(exceldate_to_pydate(d2), date(2017, 1, 17))

    def test_calendar(self):
        from datetime import date
        cal = WeekendCalendar()
        self.assertFalse(cal.is_holiday(dte(date(2017, 2, 13))))
        self.assertFalse(cal.is_holiday(dte(date(2017, 2, 14))))
        self.assertFalse(cal.is_holiday(dte(date(2017, 2, 15))))
        self.assertFalse(cal.is_holiday(dte(date(2017, 2, 16))))
        self.assertFalse(cal.is_holiday(dte(date(2017, 2, 17))))
        self.assertTrue(cal.is_holiday(dte(date(2017, 2, 18))))
        self.assertTrue(cal.is_holiday(dte(date(2017, 2, 19))))

        cal1 = EnumeratedCalendar({dte(date(2017, 2, 16))})
        self.assertTrue(cal1.is_holiday(dte(date(2017, 2, 16))))

        cal2 = EnumeratedCalendar({dte(date(2017, 2, 17))})
        self.assertTrue(cal2.is_holiday(dte(date(2017, 2, 17))))

        cal12 = union_calendars([cal1, cal2])
        self.assertTrue(cal12.is_holiday(dte(date(2017, 2, 16))))
        self.assertTrue(cal12.is_holiday(dte(date(2017, 2, 17))))

        lon_nyk = global_calendars.get("London+NewYork")
        assert isinstance(lon_nyk, EnumeratedCalendar)


class ConventionsTest(unittest.TestCase):
    def convention_test(self):
        conventions = conventions_from_file(join(dirname(__file__), 'conventions.txt'))


class InstrumentTests(unittest.TestCase):
    def test_deposit(self):
        cm = {
            'USD.LIBOR.3M': Curve('USD.LIBOR.3M', 42000 + 0, 42000 + arr(0.001, 1, 2, 200),
                                  arr([.99, .98, .975, .95]), InterpolationMode.LINEAR_LOGDF),
        }
        i = Deposit(name='USD.LIBOR.3M/Deposit/3M',
                    curve_forecast='USD.LIBOR.3M',
                    trade_date=42000 + 1,
                    start='E',
                    length=Tenor('6M'),
                    # TODO use real conventions
                    convention=Convention(Tenor("3M"), Tenor("3M"), Tenor("3M"), DCC.ACT365))
        aae(i.calc_par_rate(cm), 0.058722612773343938)

    def test_future(self):
        cm = {
            'USD.LIBOR.3M': Curve('USD.LIBOR.3M', 42000 + 0, 42000 + arr(250, 500, 750), arr(.975, .95, .92),
                                  CUBIC_LOGDF),
        }
        i = Future(name="Future",
                   curve_forecast='USD.LIBOR.3M',
                   trade_date=42000 + 1,
                   start='3F',
                   length=Tenor('3M'),
                   # TODO use real conventions
                   convention=Convention(Tenor("3M"), Tenor("3M"), Tenor("3M"), DCC.ACT360))
        aae(i.calc_par_rate(cm), 0.036277804826229887)

    def test_mtm_swap(self):
        cm = {
            'GBP.LIBOR.3M': Curve('GBP.LIBOR.3M', 42000 + 0, 42000 + arr(250, 500, 1750), arr(.945, .94, .93),
                                  CUBIC_LOGDF),
            'USD.LIBOR.3M': Curve('USD.LIBOR.3M', 42000 + 0, 42000 + arr(250, 500, 1750), arr(.975, .95, .92),
                                  CUBIC_LOGDF),
            'GBP/USD.OIS': Curve('GBP/USD.OIS', 42000 + 0, 42000 + arr(250, 500, 1750), arr(.965, .96, .94),
                                 CUBIC_LOGDF),
            'USD/USD.OIS': Curve('USD/USD.OIS', 42000 + 0, 42000 + arr(250, 500, 1750), arr(.974, .92, .91),
                                 CUBIC_LOGDF),
        }
        i = MtmCrossCurrencyBasisSwap(name="MtmCrossCurrencyBasisSwap",
                                      curve_discount_l='GBP/USD.OIS',
                                      curve_discount_r='USD/USD.OIS',
                                      curve_forecast_l='GBP.LIBOR.3M',
                                      curve_forecast_r='USD.LIBOR.3M',
                                      trade_date=42000 + 1,
                                      start='E',
                                      length=Tenor('3Y'),
                                      # TODO use real conventions
                                      convention_l=Convention(Tenor("3M"), Tenor("3M"), Tenor("3M"), DCC.ACT365),
                                      convention_r=Convention(Tenor("3M"), Tenor("3M"), Tenor("3M"), DCC.ACT360))
        aae(i.calc_par_rate(cm), -0.036300637792516029)


class PriceLadderTest(unittest.TestCase):
    def test_price_ladder(self):
        d = collections.OrderedDict((('Instrument_Z', 0), ('Instrument_A', 1), ('Instrument_B', 2), ('Else', 3)))
        ladder = PriceLadder.create(d)
        df = ladder.dataframe()
        self.assertEqual((len(df)), 4)
        self.assertEqual(list(df['Price']), [0, 1, 2, 3])
        ladder2 = PriceLadder.create(df)
        self.assertEqual(ladder, ladder2)
        instruments = ladder2.instrument_list()
        self.assertEqual(instruments, ['Instrument_Z', 'Instrument_A', 'Instrument_B', 'Else'])
        ladder3 = ladder2.sublist('Instrument')
        self.assertEqual(ladder3.instrument_list(), ['Instrument_Z', 'Instrument_A', 'Instrument_B'])


class CurveInterpolationTest(unittest.TestCase):
    def test_curve_linear_logdf(self):
        self.assertRaises(BaseException, lambda: Curve('libor', arr(0, 1), arr(1, 0.8)))
        c = Curve('libor', 0, arr(0.001, 1, 2), arr(.99, .98, .975), InterpolationMode.LINEAR_LOGDF)
        self.assertEqual(c.get_id(), 'libor')
        aae(c.get_df([0, 1, 2]), [1, .98, .975])
        aae(c.get_df([1.3, 1.9]), [0.9784973, 0.9754988])
        aae(c.get_fwd_rate_aligned(arr(1, 1.3, 1.9), ZEROFREQ, DCC.ACT365), [1.868445, 1.8698797])
        aae(c.get_fwd_rate_aligned(arr(1, 1.3, 1.9), ZEROFREQ, DCC.ACT365), [1.868445, 1.8698797])
        aae(c.get_fwd_rate(arr(1, 1.3), arr(1.3, 1.9), CONTINUOUS, DCC.ACT365),
            [1.8670117, 1.8670117])
        aae(c.get_zero_rate(arr(1), ZEROFREQ, DCC.ACT365), [(1 / .98 - 1.) * 365.])
        aae(c.get_zero_rate(arr(1), CONTINUOUS, DCC.ACT365), [-np.log(.98) * 365.])

    def test_curve_linear_cczr(self):
        self.assertRaises(BaseException, lambda: Curve('libor', arr(0, 1), arr(1, 0.8)))
        c = Curve('libor', 0, arr(0.001, 1, 2), arr(.99, .98, .975), InterpolationMode.LINEAR_CCZR)
        self.assertEqual(c.get_id(), 'libor')
        aae(c.get_df([0, 1, 2]), [1, .98, .975])
        aae(c.get_df([1.3, 1.9]), [0.9769484, 0.9748368])
        self.assertRaises(BaseException, lambda: c.get_df([3, 4]))

    def test_curve_cubic_logdf(self):
        self.assertRaises(BaseException, lambda: Curve('libor', arr([0, 1]), arr(1, 0.8)))
        c = Curve('libor', 0, arr(0.001, 1, 2), arr(.99, .98, .975), CUBIC_LOGDF)
        self.assertEqual(c.get_id(), 'libor')
        aae(c.get_df([0, 1, 2]), [1, .98, .975])
        aae(c.get_df([1.3, 1.9]), [3.845169, 2.2995965])
        # aae(c.get_df([1.3, 1.9]), [3.8450911,  2.2995577])


class CurveMapTests(unittest.TestCase):
    def test_plot(self):
        c1 = Curve('USD.LIBOR.3M', 42000 + 0, 42000 + arr(0.001, 1, 2), arr(.99, .98, .975),
                   CUBIC_LOGDF)
        c2 = Curve('USD.LIBOR.6M', 42000 + 0, 42000 + arr(0.002, 3, 4), arr(.99, .98, .975),
                   CUBIC_LOGDF)
        cm = CurveMap()
        cm.add_curve(c1)
        cm.add_curve(c2)
        self.assertEqual(len(cm), 2)
        self.assertEqual(sorted(cm.keys()), ['USD.LIBOR.3M', 'USD.LIBOR.6M'])
        # cm.plot(".*", mode=PlottingMode.DISC_FACTOR)
        # cm.plot(".*", mode=PlottingMode.ZERO_RATE)
        # cm.plot(".*", mode=PlottingMode.FWD_RATE)


class CurveConstructorTests(unittest.TestCase):
    def test_curve_construction(self):
        t = arr(42738, 47604, 52471, 57538, 62204, 67071, 71939)
        df = arr(1., 0.76592834, 0.5292694, 0.36397074, 0.24525508, 0.15913423, 0.10440653)
        self.assertRaises(BaseException, lambda: Curve('USD.LIBOR.3M', 42738, t, df, LINEAR_LOGDF))

    def test_short_rate_model(self):
        random.seed(1)
        times = [i for i in range(2, 2 + 80 * 365 + 1, 10)]
        curve = CurveConstructor.FromShortRateModel('USD.OIS', times, r0=.022, speed=0.0001, \
                                                    mean=.05, sigma=0.0005,
                                                    interpolation=InterpolationMode.LINEAR_LOGDF)

        self.assertEqual(curve.times_[0], 2)
        self.assertEqual(curve.times_[1], 12)
        self.assertEqual(curve.times_[-2], 29192)
        self.assertEqual(curve.times_[-1], 29202)
        self.assertEqual(curve.dfs_[0], 1)
        self.assertEqual(curve.dfs_[-1], 0.15920680884835336)

    def add_two_curves(self):
        random.seed(1)
        times = [i for i in range(2, 2 + 80 * 365 + 1, 10)]
        curve1 = CurveConstructor.FromShortRateModel('USD.OIS', times, r0=.022, speed=0.0001, \
                                                     mean=.05, sigma=0.0005,
                                                     interpolation=InterpolationMode.LINEAR_LOGDF)
        curve2 = CurveConstructor.FromShortRateModel('USD.OIS', times, r0=.022, speed=0.0001, \
                                                     mean=.05, sigma=0.0005,
                                                     interpolation=InterpolationMode.LINEAR_LOGDF)
        df1 = curve1.dfs_[-1]
        df2 = curve2.dfs_[-1]
        self.assertNotEqual(df1, df2)
        self.assertEqual(curve1.dfs_[-1], df1)
        curve1.add_another_curve(curve2)
        self.assertEqual(curve1.dfs_[-1], df1 * df2)
        self.assertEqual(curve2.dfs_[-1], df2)


class BuilderCompositeTests(unittest.TestCase):
    def test_builder(self):
        eval_date = 42000
        curve_builder = CurveBuilder('engine_test.xlsx', eval_date)
        self.assertEqual(curve_builder.get_curve_names(), ['USD.LIBOR.3M', 'USD.LIBOR.6M', 'USD/USD.OIS'])
        self.assertEqual(len(list(curve_builder.curve_templates)), 3)

        pricing_curvemap = CurveMap()
        s_libor3 = 'USD.LIBOR.3M'
        s_libor6 = 'USD.LIBOR.6M'
        s_ois = 'USD/USD.OIS'
        constructor = CurveConstructor.FromShortRateModel
        interp = InterpolationMode.LINEAR_LOGDF
        t = [i for i in range(eval_date + 0, eval_date + 80 * 365 + 1, 10)]

        random.seed(1)
        libor3 = constructor(s_libor3, t, r0=.022, speed=0.0001, mean=.05, sigma=0.0005, interpolation=interp)
        random.seed(2)
        libor6 = constructor(s_libor6, t, r0=.022, speed=0.0001, mean=.05, sigma=0.0005, interpolation=interp)
        random.seed(2)
        ois = constructor(s_ois, t, r0=.02, speed=0.0001, mean=-.05, sigma=0.0005, interpolation=interp)
        pricing_curvemap.add_curve(libor3)
        pricing_curvemap.add_curve(libor6)
        pricing_curvemap.add_curve(ois)
        target_prices = curve_builder.reprice(pricing_curvemap)
        self.assertEqual(len(target_prices), 101)
        self.assertEqual(type(target_prices), PriceLadder)
        build_output = curve_builder.build_curves(target_prices)
        self.assertEqual(len(build_output.output_curvemap), 3)
        test_pillars = np.linspace(eval_date + 0, eval_date + 50 * 365, 15)
        actual_libor3_df = build_output.output_curvemap[s_libor3].get_df(test_pillars)
        actual_sonia_df = build_output.output_curvemap[s_ois].get_df(test_pillars)
        expected_libor3_df = arr(1., 0.9241852, 0.8519249, 0.779718, 0.7137853,
                                 0.6571807, 0.606858, 0.5604791, 0.5197029, 0.481757,
                                 0.4462411, 0.4123829, 0.3801056, 0.3496476, 0.3209611)
        expected_sonia_df = arr(1., 0.9356349, 0.8743677, 0.8172767, 0.7655987,
                                0.7161828, 0.6701861, 0.6274215, 0.5870788, 0.5493287,
                                0.5138209, 0.479885, 0.4483417, 0.4194496, 0.3932068)

        self.maxDiff = None
        aae(actual_libor3_df, expected_libor3_df)
        aae(actual_sonia_df, expected_sonia_df)

        risk_engine = RiskCalculator(curve_builder, build_output)
        instrument_regex = "USD/.*"
        numpy.testing.assert_equal(len(risk_engine.find_instruments(instrument_regex)), 32)
        instruments_to_bump = risk_engine.find_instruments(instrument_regex)
        bumped_curves = risk_engine.get_bumped_curvemap(instruments_to_bump, 1e-4, BumpType.FULL_REBUILD)
        bumped_curves_jacobian = risk_engine.get_bumped_curvemap(instruments_to_bump, 1e-4, BumpType.JACOBIAN_REBUILD)

        numpy.testing.assert_equal(len(bumped_curves), len(bumped_curves_jacobian))

        test_pillars = np.linspace(eval_date + 30, eval_date + 50 * 365, 15)
        for curve_name in sorted(bumped_curves.keys()):
            c0 = build_output.output_curvemap[curve_name]
            c1 = bumped_curves[curve_name]
            c2 = bumped_curves_jacobian[curve_name]
            zr0 = c0.get_zero_rate(test_pillars, CONTINUOUS, DCC.ACT365)
            zr1 = c1.get_zero_rate(test_pillars, CONTINUOUS, DCC.ACT365)
            zr2 = c2.get_zero_rate(test_pillars, CONTINUOUS, DCC.ACT365)
            bumpdiff = max(abs((zr2 - zr0) / zr0))
            error = max(abs((zr2 - zr1) / zr1))
            self.assertLess(error, bumpdiff / 100.)


if __name__ == '__main__':
    if is_running_under_teamcity():
        runner = TeamcityTestRunner()
    else:
        runner = unittest.TextTestRunner()
    unittest.main(testRunner=runner)
