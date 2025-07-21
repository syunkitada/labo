import logging

from mylabo.domain import resource
from mylabo.lib.runtime import node_context

LOG = logging.getLogger(__name__)


class VM(resource.Resource):
    def __init__(self, spec):
        self.spec = spec
        self.c = node_context.NodeContext(spec)
        self.next = 0
        spec["_hostname"] = spec["name"].replace("_", "-") + "." + spec["_root_spec"]["spec"]["domain"]

    def get(self):
        print("get")

    def apply(self):
        print("apply vm\n\n", self.spec)

    def delete(self):
        print("delete vm\n\n", self.spec)
