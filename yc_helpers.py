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


def assert_type(obj, expected_type, allowNone=False):
    assert (allowNone and obj is None) or isinstance(obj, expected_type), "Unexpected type %s" % str(type(obj))


def enum_values(enum_class):
    return enum_class._member_map_

def enum_values_as_string(enum_class):
    return ','.join([x for x in enum_values(enum_class)])

def enum_from_string(enum_class, string_representation):
    if string_representation in enum_class._member_map_:
        return enum_class._member_map_[string_representation]
    else:
        raise BaseException("Unable to convert '%s' to %s. Possible values are: %s" %
                            (string_representation, str(enum_class), enum_values_as_string(enum_class)))


def assert_equal(l, r):
    assert l == r, "%s != %s" % (str(l), str(r))

def coalesce(*arg):
    for el in arg:
        if el is not None:
            return el
    return None