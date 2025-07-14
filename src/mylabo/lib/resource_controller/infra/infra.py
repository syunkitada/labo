import logging
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

from mylabo.domain import resource
from mylabo.lib.resource_controller.vm import vm
from mylabo.lib.runtime import runtime_context

LOG = logging.getLogger(__name__)


class Infra(resource.Resource):
    def __init__(self):
        pass

    def get(self, ctx, spec):
        print("get")

    def apply(self, ctx, spec):
        print("apply", spec)
        spec = spec["spec"]

        results = OrderedDict()
        node_ctxs = []

        def init_node_ctx(node_spec):
            node_ctx = runtime_context.new(node_spec)
            if node_spec["kind"] == "vm":
                resource = vm.VM()

            # results[rspec["name"]] = []

            # for child in rspec.get("childs", []):
            #     init_node_ctx(child)

        for node_spec in spec.get("nodes", []):
            init_node_ctx(node_spec)

        # while True:
        #     with ThreadPoolExecutor(max_workers=parallel_pool_size) as pool:
        #         tmp_results = pool.map(node_manager.make, node_ctxs)
        #     for result in tmp_results:
        #         results[result["name"]].append(result["result"])

        #     next_node_ctxs = []
        #     for t in node_ctxs:
        #         # nextがインクリメントされたnode_ctxsのみ次のタスクを実行します
        #         if t.next > 0:
        #             next_node_ctxs.append(t)
        #     if len(next_node_ctxs) == 0:
        #         break
        #     node_ctxs = next_node_ctxs

    def delete(self, ctx, spec):
        print("delete")
