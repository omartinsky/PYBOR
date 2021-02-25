# Copyright © 2017 Ondrej Martinsky, All rights reserved
# http://github.com/omartinsky/pybor
from dataclasses import dataclass
from os.path import join, dirname

from yc_date import *
from pandas import *
import enum, os
import pandas as pd

from yc_helpers import enum_from_string, assert_type


class DCC(enum.Enum):
    ACT365 = 0
    ACT360 = 1

    def get_denominator(self):
        if self == DCC.ACT360:
            return 360.
        elif self == DCC.ACT365:
            return 365.
        assert False


class CalculationType(enum.Enum):
    PLAIN = 0
    AVERAGING = 1
    NONE = 2


class CouponFreq(enum.Enum):
    CONTINUOUS = 0
    DAILY = 1
    QUARTERLY = 2
    ZEROFREQ = 3


CONTINUOUS = CouponFreq.CONTINUOUS
DAILY = CouponFreq.DAILY
QUARTERLY = CouponFreq.QUARTERLY
ZEROFREQ = CouponFreq.ZEROFREQ


@dataclass
class Convention:
    reset_frequency: Tenor
    calculation_frequency: Tenor
    payment_frequency: Tenor
    dcc: DCC


class Conventions:
    def __init__(self):
        self.map = dict()

    def get(self, convention_name):
        if convention_name not in self.map:
            raise BaseException("Unable to get convention %s" % convention_name)
        return self.map[convention_name]


def conventions_from_file(file: str) -> Conventions:
    """
    Notes:
    Reset Frequency < Calculation Period Frequency indicates averaging / OIS leg
    Calculation Period Frequency < Payment Frequency indicates compounting leg
    """
    conventions = Conventions()
    conventions.map = dict()
    assert os.path.exists(file)
    dataframe = pd.read_csv(file, delimiter='\t')
    for index, row in dataframe.iterrows():
        conv = Convention(
            reset_frequency=Tenor(row['Reset Frequency']),
            calculation_frequency=Tenor(row['Calculation Period Frequency']),
            payment_frequency=Tenor(row['Payment Frequency']),
            dcc=enum_from_string(DCC, row['Day Count Convention']),
        )
        assert index not in conventions.map
        conventions.map[row['Index']] = conv
    return conventions


global_conventions = conventions_from_file(join(dirname(__file__), 'conventions.txt'))
