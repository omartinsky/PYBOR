# Copyright © 2017 Ondrej Martinsky, All rights reserved
# http://github.com/omartinsky/pybor

from instruments.deposit import *
from instruments.zerorate import *
from instruments.future import *
from instruments.basisswap import *
from instruments.crosscurrencyswap import *
from instruments.swap import *
from instruments.termdeposit import *
from instruments.mtmcrosscurrencybasisswap import *
import numpy
from collections import OrderedDict, defaultdict

from pandas import *
import scipy.optimize
import copy, os


def coalesce(*arg):
    for el in arg:
        if el is not None:
            return el
    return None


class CurveTemplate:
    def __init__(self, curve_name):
        self.curve_name = curve_name
        self.instruments = []


class ProgressMonitor:
    def __init__(self):
        self.counter = 0

    def reset(self):
        self.counter = 0

    def update(self):
        self.counter += 1
        if self.counter % 100 == 0:
            print('%i' % self.counter, end='', flush=True)
        elif self.counter % 10 == 0:
            print('.', end='', flush=True)


class BuildOutput:
    def __init__(self, input_prices, output_curvemap, jacobian_dIdP, instruments):
        self.input_prices = input_prices
        self.output_curvemap = output_curvemap
        self.jacobian_dIdP = jacobian_dIdP
        self.instruments = instruments

class PriceLadder(collections.OrderedDict):
    def create(data):
        if isinstance(data, pandas.DataFrame):
            od = collections.OrderedDict(data['Price'])
            return PriceLadder(od)
        elif isinstance(data, dict):
            return PriceLadder(data)
        else:
            raise BaseException("Unknown data type %s" % type(data))

    def instrument_list(self):
        return list(self.keys())

    def sublist(self, instrument_regex):
        l = []
        for k, v in self.items():
            if re.match(instrument_regex, k):
                l.append((k,v))
        return PriceLadder.create(OrderedDict(l))

    def dataframe(self):
        df = DataFrame.from_dict(self, orient='index')
        df.columns=['Price']
        return df


def calc_residual(curvemap, instrument_prices, instrument):
    r_actual = instrument.calc_par_rate(curvemap)
    price = instrument_prices[instrument.name_]
    r_target = instrument.par_rate_from_price(price)
    return r_actual - r_target

def calc_residuals(dofs, curve_builder, curvemap, instrument_prices, curves_for_stage, instruments_for_stage):
    if curve_builder.progress_monitor:
        curve_builder.progress_monitor.update()
    assert not numpy.isnan(dofs).any()
    curvemap.set_all_dofs(curves_for_stage, dofs)

    y = [calc_residual(curvemap, instrument_prices, i) for i in instruments_for_stage]
    return y

class CurveBuilder:
    def __init__(self, excel_file, eval_date, progress_monitor=None):
        assert os.path.exists(excel_file)
        xl = ExcelFile(excel_file)
        self.df_instruments = xl.parse('Instrument Properties', index_col='Name', parse_cols='A:L')
        self.df_curves = xl.parse('Curve Properties', index_col='Curve', parse_cols='A:C')
        if (len(self.df_curves) == 0):
            raise BaseException("No curves found in spreadsheet")
        self.curve_templates = list()
        self.progress_monitor = progress_monitor
        self.eval_date = eval_date

        self.all_instruments = list()
        self.instrument_positions = dict()

        for curve_name in list(self.df_curves.index):  # Order of curves determined by XLS file:
            curve_template = CurveTemplate(curve_name)

            curve_df = self.df_instruments[
                self.df_instruments['Curve'] == curve_name]  # Order of instruments determined by XLS file
            for name, row in curve_df.iterrows():
                try:
                    instrument_type = row['Type']
                    assert isinstance(row, pandas.core.series.Series)
                    fcastL = row['Forecast Curve Left']
                    fcastR = row['Forecast Curve Right']
                    discL = row['Discount Curve Left']
                    discR = row['Discount Curve Right']
                    convL = row['Convention Left']
                    convR = row['Convention Right']
                    start = row['Start']
                    length = row['Length']
                    enabled = row['Enabled']
                    assert enabled in 'YN'
                    if enabled == 'N':
                        continue

                    if instrument_type == 'Deposit':
                        inst = Deposit.CreateFromDataFrameRow(name, eval_date, row)
                    elif instrument_type == 'ZeroRate':
                        inst = ZeroRate.CreateFromDataFrameRow(name, eval_date, row)
                    elif instrument_type == 'Future':
                        inst = Future.CreateFromDataFrameRow(name, eval_date, row)
                    elif instrument_type == 'Swap':
                        inst = Swap.CreateFromDataFrameRow(name, eval_date, row)
                    elif instrument_type == 'BasisSwap':
                        inst = BasisSwap.CreateFromDataFrameRow(name, eval_date, row)
                    elif instrument_type == 'CrossCurrencySwap':
                        inst = CrossCurrencySwap.CreateFromDataFrameRow(name, eval_date, row)
                    elif instrument_type == 'MtmCrossCurrencyBasisSwap':
                        inst = MtmCrossCurrencyBasisSwap.CreateFromDataFrameRow(name, eval_date, row)
                    elif instrument_type == 'TermDeposit':
                        inst = TermDeposit.CreateFromDataFrameRow(name, eval_date, row)
                    else:
                        raise BaseException("Unknown instrument type %s" % instrument_type)
                except BaseException as ex:
                    raise BaseException("Error processing instrument %s" % name) from ex

                self.instrument_positions[inst.get_name()] = len(self.all_instruments)
                self.all_instruments.append(inst)
                curve_template.instruments.append(inst)

            if len(curve_template.instruments) == 0:
                raise BaseException("No instruments found for curve template %s" % curve_template.curve_name)

            self.curve_templates.append(curve_template)
        pass

    def get_solve_stages(self):
        map = defaultdict(set)
        for row in self.df_curves.iterrows():
            curve, stage = row[0], row[1]['Solve Stage']
            map[stage].add(curve)
        stages = [map[i] for i in list(sorted(map))]
        return stages

    def get_curve_names(self):
        return [t.curve_name for t in self.curve_templates]

    def get_instruments_for_stage(self, curves_for_stage):
        instruments_for_stage = []
        for curve_template in self.curve_templates:
            if curve_template.curve_name in curves_for_stage:
                for i in curve_template.instruments:  # TODO get rid of this loop
                    instruments_for_stage.append(i)
        return instruments_for_stage

    def reprice(self, curvemap):
        out = OrderedDict()
        for curve_template in self.curve_templates:
            for instrument in curve_template.instruments:
                if (curvemap):
                    rate = instrument.calc_par_rate(curvemap)
                    out[instrument.name_] = instrument.price_from_par_rate(rate)
                else: # If curvemap is not provided, generated price ladder will contain zeros.
                    out[instrument.name_] = 0.0
        return PriceLadder(out)

    def get_instrument_rates(self, price_ladder):
        maturities = [self.get_instrument_by_name(name).get_pillar_date() for name in price_ladder.keys()]
        rates = [self.get_instrument_by_name(name).par_rate_from_price(price) for name, price in price_ladder.items()]
        return array(maturities), array(rates)

    def parse_instrument_prices(self, prices):
        if isinstance(prices, dict):
            return prices
        elif isinstance(prices, pandas.DataFrame):
            try:
                return dict(zip(prices['Instrument'], prices['Price']))
            except BaseException as ex:
                raise BaseException("Unable to parse dataframe with instrument prices") from ex
        else:
            raise BaseException("Unknown type")

    def create_initial_curvemap(self, initial_rate):
        pillar_count = 0
        curvemap = CurveMap()
        for curve_template in self.curve_templates:
            pillar = []
            for instrument in curve_template.instruments:
                pillar_date = instrument.get_pillar_date()
                pillar.append(pillar_date)
            pillar = array(sorted(set(pillar)))
            assert len(pillar) > 0, "Pillars are empty"
            dfs = exp(-initial_rate * (pillar - self.eval_date) / 365.)  # initial rates will be circa 2%
            curve_name = curve_template.curve_name
            interpolation = enum_from_string(InterpolationMode, self.df_curves.loc[curve_name].Interpolation)
            #print("Creating pillars %i - %i for curve %s" % (pillar_count, pillar_count + len(pillar), curve_name))
            pillar_count += len(pillar)
            curve = Curve(curve_name, self.eval_date, pillar, dfs, interpolation)
            curvemap.add_curve(curve)
        return curvemap

    def build_curves(self, instrument_prices):
        instrument_prices = self.parse_instrument_prices(instrument_prices)

        curvemap = self.create_initial_curvemap(0.02)   # Create unoptimized curve map

        stages = self.get_solve_stages()

        for iStage, curves_for_stage in enumerate(stages):
            instruments_for_stage = self.get_instruments_for_stage(curves_for_stage)
            dofs = curvemap.get_all_dofs(curves_for_stage)
            print("Solving stage %i/%i containing curves %s (%i pillars)" % (iStage+1, len(stages), ", ".join(sorted(curves_for_stage)), len(dofs)))

            if (self.progress_monitor):
                self.progress_monitor.reset()

            arguments = (self, curvemap, instrument_prices, curves_for_stage, instruments_for_stage)
            bounds = (zeros(len(dofs)), numpy.inf * ones(len(dofs)))
            solution = scipy.optimize.least_squares(fun=calc_residuals, x0=dofs, args=arguments, bounds=bounds)

            assert isinstance(solution, scipy.optimize.OptimizeResult)

            if not solution.success:
                raise BaseException(solution.message)
            curvemap.set_all_dofs(curves_for_stage, solution.x)

        # calculate jacobian matrix
        bump_size = 1e-8
        final_solution = curvemap.get_all_dofs(curvemap.keys())
        all_curves = [curve_template.curve_name for curve_template in self.curve_templates]
        all_instruments = self.get_instruments_for_stage(all_curves)
        arguments = (self, curvemap, instrument_prices, all_curves, all_instruments)
        e0 = array(calc_residuals(final_solution, *arguments))
        jacobian_dIdP = []
        for i in range(len(final_solution)):
            bump_vector = zeros(len(final_solution))
            bump_vector[i] += bump_size
            e = array(calc_residuals(final_solution + bump_vector, *arguments))
            jacobian_dIdP.append((e - e0) / bump_size)
        # this jacobian_dIdP contains dI/dP.  Rows=Pillars  Cols=Instruments
        # after inversion, it will contain dP/dI.   Rows=Instruments   Cols=Pillars
        jacobian_dIdP = matrix(jacobian_dIdP)

        print("Done")
        return BuildOutput(instrument_prices, curvemap, jacobian_dIdP, self.all_instruments)

    def get_instrument_by_name(self, name):
        pos = self.instrument_positions[name]
        return self.all_instruments[pos]

