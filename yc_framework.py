# Copyright © 2017 Ondrej Martinsky, All rights reserved
# http://github.com/omartinsky/pybor

from yc_curvebuilder import *
from yc_curve import *
from yc_riskcalculator import *
from copy import deepcopy
import re, random

seterr(invalid='raise')  # catch moment when math.nan is generated
