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


import unittest
from teamcity import is_running_under_teamcity
from teamcity.unittestpy import TeamcityTestRunner

from yc_framework import *
from yc_convention import *
import numpy, random

aae = numpy.testing.assert_almost_equal

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
        self.assertEqual(t.n, 3)
        self.assertEqual(t.unit, 'M')

    def test_date_conversion(self):
        p = date(1970, 1, 3)
        d = toexceldate(p)
        self.assertEqual(d, 2)
        self.assertEqual(fromexceldate(d), date(1970, 1, 3))

    def test_date_creation(self):
        self.assertEqual(create_date(43000), 43000)
        self.assertEqual(create_date('E', 43000), 43000)
        self.assertEqual(create_date('1M', 43000), 43030)
        self.assertEqual(create_date('E+1M', 43000), 43030)
        self.assertEqual(create_date('E+E+1Y+1M', 43000), 43396)
        self.assertEqual(create_date('1970-01-03'), 2)

    def test_dcc(self):
        ACT360 = DCC.ACT360
        ACT365 = DCC.ACT365
        self.assertEqual(calculate_dcf(create_date('1995-01-01'), create_date('1996-01-01'), ACT365), 1)
        self.assertEqual(calculate_dcf(create_date('1996-01-01'), create_date('1997-01-01'), ACT365), 366/365)
        self.assertEqual(calculate_dcf(create_date('1996-01-01'), create_date('1997-01-01'), ACT360), 366/360)

class InstrumentTests(unittest.TestCase):
    def test_deposit(self):
        cm = {
            'USDLIBOR3M' : Curve('USDLIBOR3M', 0, array([0.001, 1, 2, 200]), array([.99, .98, .975, .95]), InterpolationMode.LINEAR_LOGDF),
        }
        i = Deposit(name='USDLIBOR3M/Deposit/3M',
                    curve_forecast='USDLIBOR3M',
                    start=create_date('E', 1),
                    len=Tenor('6M'))
        aae(i.calc_par_rate(cm), .058774765557153198)

class PriceLadderTest(unittest.TestCase):
    def test_price_ladder(self):
        d = collections.OrderedDict({ 'Instrument_Z': 0, 'Instrument_A': 1, 'Instrument_B': 2, 'Else': 3})
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
        self.assertRaises(BaseException, lambda: Curve('libor', array([0, 1]), array([1, 0.8])))
        c = Curve('libor', 0, array([0.001, 1, 2]), array([.99, .98, .975]), InterpolationMode.LINEAR_LOGDF)
        self.assertEqual(c.get_id(), 'libor')
        aae(c.get_df([0, 1, 2]), [1, .98, .975])
        aae(c.get_df([1.3, 1.9]), [0.9784973, 0.9754988])
        aae(c.get_rate(array([1, 1.3, 1.9]), CouponFreq.ZERO, DCC.ACT365), [1.868445, 1.8698797])

    def test_curve_linear_cczr(self):
        self.assertRaises(BaseException, lambda: Curve('libor', array([0, 1]), array([1, 0.8])))
        c = Curve('libor', 0, array([0.001, 1, 2]), array([.99, .98, .975]), InterpolationMode.LINEAR_CCZR)
        self.assertEqual(c.get_id(), 'libor')
        aae(c.get_df([0, 1, 2]), [1, .98, .975])
        aae(c.get_df([1.3, 1.9]), [0.9769484, 0.9748368])

    def test_curve_cubic_logdf(self):
        self.assertRaises(BaseException, lambda: Curve('libor', array([0, 1]), array([1, 0.8])))
        c = Curve('libor', 0, array([0.001, 1, 2]), array([.99, .98, .975]), InterpolationMode.CUBIC_LOGDF)
        self.assertEqual(c.get_id(), 'libor')
        aae(c.get_df([0, 1, 2]), [1, .98, .975])
        aae(c.get_df([1.3, 1.9]), [3.845169 ,  2.2995965])
        #aae(c.get_df([1.3, 1.9]), [3.8450911,  2.2995577])  

class CurveConstructorTests(unittest.TestCase):
    def test_short_rate_model(self):
        random.seed(1)
        times = [i for i in range(2, 2+80*365+1, 10)]
        curve = CurveConstructor.FromShortRateModel('USDOIS', times, r0=.022, speed=0.0001, \
                             mean=.05, sigma=0.0005, interpolation=InterpolationMode.LINEAR_LOGDF)

        self.assertEqual(curve.times_[0], 2)
        self.assertEqual(curve.times_[1], 12)
        self.assertEqual(curve.times_[-2], 29192)
        self.assertEqual(curve.times_[-1], 29202)
        self.assertEqual(curve.dfs_[0], 1)
        self.assertEqual(curve.dfs_[-1], 0.15920680884835336)

    def add_two_curves(self):
        random.seed(1)
        times = [i for i in range(2, 2+80*365+1, 10)]
        curve1 = CurveConstructor.FromShortRateModel('USDOIS', times, r0=.022, speed=0.0001, \
                             mean=.05, sigma=0.0005, interpolation=InterpolationMode.LINEAR_LOGDF)
        curve2 = CurveConstructor.FromShortRateModel('USDOIS', times, r0=.022, speed=0.0001, \
                             mean=.05, sigma=0.0005, interpolation=InterpolationMode.LINEAR_LOGDF)
        df1 = curve1.dfs_[-1]
        df2 = curve2.dfs_[-1]
        self.assertNotEqual(df1,df2)
        self.assertEqual(curve1.dfs_[-1], df1)
        curve1.add_another_curve(curve2)
        self.assertEqual(curve1.dfs_[-1], df1*df2)
        self.assertEqual(curve2.dfs_[-1], df2)


class BuilderCompositeTests(unittest.TestCase):
    def test_builder(self):
        eval_date = toexceldate(date(1970, 1, 1))
        curve_builder = CurveBuilder('engine_test.xlsx', eval_date)
        self.assertEqual(curve_builder.get_curve_names(), ['USDLIBOR3M', 'USDLIBOR6M', 'USD-USDOIS'])
        self.assertEqual(len(list(curve_builder.curve_templates)), 3)
        self.assertIsNotNone(curve_builder.getframe())

        pricing_curvemap = CurveMap()
        s_libor3 = 'USDLIBOR3M'
        s_libor6 = 'USDLIBOR6M'
        s_ois = 'USD-USDOIS'
        constructor = CurveConstructor.FromShortRateModel
        interp = InterpolationMode.LINEAR_LOGDF
        t = [i for i in range(0, 80*365+1, 10)]

        random.seed(1)
        libor3 = constructor(s_libor3, t, r0=.022, speed=0.0001, mean=.05, sigma=0.0005, interpolation=interp)
        random.seed(2)
        libor6 = constructor(s_libor6, t, r0=.022, speed=0.0001, mean=.05, sigma=0.0005, interpolation=interp)
        random.seed(2)
        sonia = constructor(s_ois, t, r0=.02, speed=0.0001, mean=-.05, sigma=0.0005, interpolation=interp)
        pricing_curvemap.add_curve(libor3)
        pricing_curvemap.add_curve(libor6)
        pricing_curvemap.add_curve(sonia)
        target_prices = curve_builder.reprice(pricing_curvemap)
        self.assertEqual(len(target_prices), 101)
        self.assertEqual(type(target_prices), PriceLadder)
        build_output = curve_builder.build_curves(target_prices)
        self.assertEqual(len(build_output.output_curvemap), 3)
        actual_libor3_df = build_output.output_curvemap[s_libor3].get_df(linspace(0, 80, 15))
        actual_sonia_df = build_output.output_curvemap[s_ois].get_df(linspace(0, 80, 15))
        expected_libor3_df = array([1.0, 0.999654297582, 0.999308714674, 0.998963251235, 0.998617907224, 0.998272682599,
                                    0.997927577319, 0.997582591342, 0.997237724628, 0.996892977136, 0.996548348823,
                                    0.996203839649, 0.995859449573, 0.995515178553, 0.995171026549])
        expected_sonia_df = array([1.0, 0.999685632814, 0.999371371753, 0.999057209484, 0.998743145974, 0.998429181193,
                                   0.998114926351, 0.997800483168, 0.997486139045, 0.997171893953, 0.996857747859,
                                   0.996542988182, 0.996227984919, 0.995913081227, 0.995598277075])

        self.maxDiff = None
        aae(actual_libor3_df, expected_libor3_df)
        aae(actual_sonia_df, expected_sonia_df)

        risk_engine = RiskCalculator(curve_builder, build_output)
        instrument_regex = "USD\-.*"
        numpy.testing.assert_equal(len(risk_engine.find_instruments(instrument_regex)), 32)
        instruments_to_bump = risk_engine.find_instruments(instrument_regex)
        bumped_curves = risk_engine.get_bumped_curvemap(instruments_to_bump, 1e-4, BumpType.FULL_REBUILD)
        bumped_curves_jacobian = risk_engine.get_bumped_curvemap(instruments_to_bump, 1e-4, BumpType.JACOBIAN_REBUILD)

        numpy.testing.assert_equal(len(bumped_curves), len(bumped_curves_jacobian))


        for curve_name in sorted(bumped_curves):
            c1 = bumped_curves[curve_name]
            c2 = bumped_curves_jacobian[curve_name]
            df1 = c1.get_df(linspace(0,80,15))
            df2 = c2.get_df(linspace(0,80,15))
            aae(df1, df2)

if __name__ == '__main__':
    if is_running_under_teamcity():
        runner = TeamcityTestRunner()
    else:
        runner = unittest.TextTestRunner()
    unittest.main(testRunner=runner)