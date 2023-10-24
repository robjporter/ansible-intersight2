import sys

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")


def get_type(var, **kwargs):
    return str(type(var))


class FilterModule(object):
    def filters(self):
        return {
            "get_type": get_type
        }
