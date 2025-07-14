import logging

from mylabo.domain import resource

LOG = logging.getLogger(__name__)


class Container(resource.Resource):
    def __init__(self):
        pass

    def get(self, ctx, spec):
        print("get")

    def apply(self, ctx, spec):
        print("apply", spec)

    def delete(self, ctx, spec):
        print("delete")
