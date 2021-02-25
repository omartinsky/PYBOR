# Copyright © 2017 Ondrej Martinsky, All rights reserved
# http://github.com/omartinsky/pybor

import copy
import enum
import re
from typing import List

import numpy as np

from yc_curvebuilder import BuildOutput, CurveBuilder


class BumpType(enum.Enum):
    FULL_REBUILD = 0
    JACOBIAN_REBUILD = 1


class RiskCalculator:
    def __init__(self, curve_engine, build_output: BuildOutput):
        assert isinstance(curve_engine, CurveBuilder)
        assert isinstance(build_output, BuildOutput)
        self.curve_engine = curve_engine
        self.build_output = build_output
        self.cache = dict()

    def find_instruments(self, instrument_regex):
        bumped_instruments = list()
        for name in sorted(self.build_output.input_prices.keys()):
            if re.match(instrument_regex, name):
                bumped_instruments.append(name)
        if len(bumped_instruments) == 0:
            raise BaseException("Regex pattern %s corresponds to no instruments" % instrument_regex)
        return bumped_instruments

    def get_bumped_curvemap(self, instrument_list, par_rate_bump_amount, bump_type):
        if bump_type == BumpType.FULL_REBUILD:
            return self.get_bumped_curvemap_full(instrument_list, par_rate_bump_amount)
        elif bump_type == BumpType.JACOBIAN_REBUILD:
            return self.get_bumped_curvemap_jacobian(instrument_list, par_rate_bump_amount)
        else:
            raise BaseException("Unknown bump type")

    def get_bumped_curvemap_full(self, instrument_list, par_rate_bump_amount):

        key = (tuple(instrument_list), par_rate_bump_amount)

        if key in self.cache:
            return self.cache[key]

        bumped_prices = copy.deepcopy(self.build_output.input_prices)
        for name, value in bumped_prices.items():
            if name in instrument_list:
                drdp = self.curve_engine.get_instrument_by_name(name).drdp()
                price_bump_amount = par_rate_bump_amount * drdp
                bumped_prices[name] += price_bump_amount

        bumped_build_output = self.curve_engine.build_curves(bumped_prices)
        self.cache[key] = bumped_build_output.output_curvemap
        return bumped_build_output.output_curvemap

    def get_bumped_curvemap_jacobian(self,
                                     instrument_list: List,
                                     par_rate_bump_amount):
        par_rate_bumps = np.zeros(len(self.build_output.instruments))
        instrument_names = [i.get_name() for i in self.build_output.instruments]
        for instrument_name in instrument_list:
            ix = instrument_names.index(instrument_name)
            par_rate_bumps[ix] = par_rate_bump_amount

        jacobian_dPdI = np.linalg.pinv(self.build_output.jacobian_dIdP)
        curvemap_bumped = copy.deepcopy(self.build_output.output_curvemap)

        responses = np.dot(par_rate_bumps, jacobian_dPdI)

        dfs = curvemap_bumped.get_all_dofs(curvemap_bumped.keys())
        dfs += responses
        curvemap_bumped.set_all_dofs(curvemap_bumped.keys(), dfs)

        return curvemap_bumped
