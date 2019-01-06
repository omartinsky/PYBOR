# Copyright © 2017 Ondrej Martinsky, All rights reserved
# http://github.com/omartinsky/pybor

def assertRaisesMessage(exception_class, lambda_function, message_substring):
    try:
        lambda_function()
    except exception_class as ex:
        msg = ex.args[0]
        if message_substring not in msg:
            raise BaseException("Unexpected exception string '%s'" % msg)

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