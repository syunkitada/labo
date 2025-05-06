import logging

from mylabo.domain import resource

LOG = logging.getLogger(__name__)


def size_str_to_float(size_str):
    if size_str[-1] == "G":
        return float(size_str[:-1]) * 1024 * 1024 * 1024
    elif size_str[-1] == "M":
        return float(size_str[:-1]) * 1024 * 1024
    elif size_str[-1] == "K":
        return float(size_str[:-1]) * 1024
    return int(size_str)


class VMImage(resource.Resource):
    def __init__(self):
        pass

    def get(self, ctx, spec):
        print("get")

    def apply(self, ctx, spec):
        print("apply")

    def delete(self, ctx, spec):
        print("delete")
