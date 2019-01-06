# Copyright © 2017 Ondrej Martinsky, All rights reserved
# http://github.com/omartinsky/pybor

from yc_date import *
from pandas import *
import enum, os


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
    ZERO = 3

class Convention:
    def __init__(self, reset_frequency, calculation_frequency, payment_frequency, dcc):
        assert_type(reset_frequency, Tenor)
        assert_type(calculation_frequency, Tenor)
        assert_type(payment_frequency, Tenor)
        assert_type(dcc, DCC)
        self.reset_frequency = reset_frequency
        self.calculation_frequency = calculation_frequency
        self.payment_frequency = payment_frequency
        self.dcc = dcc

class Conventions:
    def __init__(self):
        self.map = dict()

    def FromSpreadsheet(excel_file):
        conventions = Conventions()
        conventions.map = dict()
        assert os.path.exists(excel_file)
        xl = ExcelFile(excel_file)
        dataframe = xl.parse('Conventions', index_col='Index', parse_cols='A:E')
        for index, row in dataframe.iterrows():
            conv = Convention(
                reset_frequency = Tenor(row['Reset Frequency']),
                calculation_frequency = Tenor(row['Calculation Period Frequency']),
                payment_frequency = Tenor(row['Payment Frequency']),
                dcc = enum_from_string(DCC, row['Day Count Convention']),
            )
            assert index not in conventions.map
            conventions.map[index] = conv
        return conventions

    def get(self, convention_name):
        if convention_name not in self.map:
            raise BaseException("Unable to get convention %s" % convention_name)
        return self.map[convention_name]

global_conventions = Conventions.FromSpreadsheet('conventions.xlsx')