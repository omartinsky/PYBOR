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


from yc_framework import *
import pylab

curve_builder = CurveBuilder('engine_example.xlsx', 0, progress_monitor=ProgressMonitor())


def create_curvemap():
    pricing_curvemap = CurveMap()
    usdlibor3_name = 'USD-LIBOR-3M'
    usdlibor6_name = 'USD-LIBOR-6M'
    usdois_name = 'USD-DISC/USD-OIS-1B'
    daystart, daystep, dayend = 0, 10, 365 * 80
    modelCreate = CurveConstructor.FromShortRateModel
    usdlibor3 = modelCreate('USD-LIBOR-3M', daystart, daystep, dayend, \
                            r0=.006, speed=0.03, mean=.035, sigma=1e-4, interpolation=InterpolationMode.LINEAR_LOGDF,
                            random_seed=1)
    usdlibor6 = modelCreate('USD-LIBOR-6M', daystart, daystep, dayend, \
                            r0=.015, speed=0.02, mean=.045, sigma=1e-4, interpolation=InterpolationMode.LINEAR_LOGDF,
                            random_seed=2)
    usdlibor12 = modelCreate('USD-LIBOR-12M', daystart, daystep, dayend, \
                             r0=.020, speed=0.02, mean=.065, sigma=1e-4, interpolation=InterpolationMode.LINEAR_LOGDF,
                             random_seed=2)
    gbplibor3 = modelCreate('GBP-LIBOR-3M', daystart, daystep, dayend, \
                            r0=.02, speed=0.03, mean=0.03, sigma=1e-4, interpolation=InterpolationMode.LINEAR_LOGDF,
                            random_seed=5)
    gbpsonia = modelCreate('GBP-DISC/GBP-SONIA-1B', daystart, daystep, dayend, \
                           r0=.015, speed=0.03, mean=0.020, sigma=1e-4, interpolation=InterpolationMode.LINEAR_LOGDF,
                           random_seed=6)
    gbpois = modelCreate('GBP-DISC/USD-OIS-1B', daystart, daystep, dayend, \
                         r0=.018, speed=0.03, mean=0.015, sigma=1e-4, interpolation=InterpolationMode.LINEAR_LOGDF,
                         random_seed=4)
    usdois = modelCreate('USD-DISC/USD-OIS-1B', daystart, daystep, dayend, \
                         r0=.012, speed=0.003, mean=0.022, sigma=1e-4, interpolation=InterpolationMode.LINEAR_LOGDF,
                         random_seed=3)
    pricing_curvemap.add_curve(usdlibor3)
    pricing_curvemap.add_curve(usdlibor6)
    pricing_curvemap.add_curve(usdlibor12)
    pricing_curvemap.add_curve(gbplibor3)
    pricing_curvemap.add_curve(gbpois)
    pricing_curvemap.add_curve(gbpsonia)
    pricing_curvemap.add_curve(usdois)
    return pricing_curvemap


pricing_curvemap = create_curvemap()
prices = curve_builder.reprice(pricing_curvemap)

print("**** Building curves from template instruments")
build_output = curve_builder.build_curves(prices)