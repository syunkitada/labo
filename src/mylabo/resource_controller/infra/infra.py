import os
import logging
from fabric import Connection
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
import traceback

from mylabo.domain import resource
from mylabo.resource_controller.container import container
from mylabo.resource_controller.vm import vm
from mylabo.lib import colors
from mylabo.lib.context import context
from mylabo.lib.runtime import runtime_context

LOG = logging.getLogger(__name__)


class Infra(resource.Resource):
    def __init__(self, ctx: context.Context, manifest: dict):
        self.ctx = ctx
        self.c = runtime_context.new(manifest)
        self.manifest = manifest
        self.spec = manifest["spec"]
        self.next = 0
        self.parallel_pool_size = 1  # TODO : Make this configurable

    def get(self):
        results = []
        for node_manifest in self.spec.get("nodes", []):
            node_manifest["_root_manifest"] = self.manifest
            if node_manifest["kind"] == "vm":
                node = vm.VM(node_manifest)
            elif node_manifest["kind"] == "container":
                node = container.Container(node_manifest)
            else:
                raise ValueError(f"Unsupported node kind: {node_manifest['kind']}")

            results.append(node.get())

        return results

    def _init_nodes(self, manifest):
        results = OrderedDict()
        nodes = []

        def _init(manifest):
            for node_manifest in manifest["spec"].get("nodes", []):
                label_name = self.ctx.labels.get("name")
                if label_name is not None and node_manifest["name"] != label_name:
                    continue

                node_manifest["_root_manifest"] = self.manifest
                if node_manifest["kind"] == "vm":
                    node = vm.VM(self.ctx, node_manifest)
                elif node_manifest["kind"] == "container":
                    node = container.Container(self.ctx, node_manifest)
                else:
                    raise ValueError(f"Unsupported node kind: {node_manifest['kind']}")

                results[node_manifest["name"]] = []
                nodes.append(node)

                _init(node_manifest)

        _init(manifest)

        return nodes, results

    def apply(self):
        print("apply", self.manifest)

        nodes, results = self._init_nodes(self.manifest)

        os.makedirs(self.manifest["_script_dir"], exist_ok=True)
        while True:
            with ThreadPoolExecutor(max_workers=self.parallel_pool_size) as pool:
                tmp_results = pool.map(_apply, nodes)
            for result in tmp_results:
                results[result["name"]].append(result["result"])

            next_node_ctxs = []
            for t in nodes:
                # nextがインクリメントされたnode_ctxsのみ次のタスクを実行します
                if t.next > 0:
                    next_node_ctxs.append(t)
            if len(next_node_ctxs) == 0:
                break
            nodes = next_node_ctxs

        _print_results(results)
        _dump_scripts(self.manifest, "apply", nodes)

    def delete(self):
        nodes, results = self._init_nodes(self.manifest)

        os.makedirs(self.manifest["_script_dir"], exist_ok=True)
        while True:
            with ThreadPoolExecutor(max_workers=self.parallel_pool_size) as pool:
                tmp_results = pool.map(_delete, nodes)
            for result in tmp_results:
                results[result["name"]].append(result["result"])

            next_node_ctxs = []
            for t in nodes:
                # nextがインクリメントされたnode_ctxsのみ次のタスクを実行します
                if t.next > 0:
                    next_node_ctxs.append(t)
            if len(next_node_ctxs) == 0:
                break
            nodes = next_node_ctxs

        _print_results(results)
        _dump_scripts(self.manifest, "apply", nodes)

    def test(self):
        print("test", self.manifest)

        nodes, results = self._init_nodes(self.manifest)

        os.makedirs(self.manifest["_script_dir"], exist_ok=True)
        while True:
            with ThreadPoolExecutor(max_workers=self.parallel_pool_size) as pool:
                tmp_results = pool.map(_test, nodes)
            for result in tmp_results:
                results[result["name"]].append(result["result"])

            next_node_ctxs = []
            for t in nodes:
                # nextがインクリメントされたnode_ctxsのみ次のタスクを実行します
                if t.next > 0:
                    next_node_ctxs.append(t)
            if len(next_node_ctxs) == 0:
                break
            nodes = next_node_ctxs

        _print_results(results)
        _dump_scripts(self.manifest, "test", nodes)

    def any(self, action: resource.AnyAction):
        pass


def _test(node, cmd=""):
    print(f"{cmd} node {node.manifest['name']}: start {node.next}")
    result = None
    try:
        result = node.test()
    except Exception as e:
        result = {"status": 1, "msg": colors.crit(f"{str(e)}\n{traceback.format_exc()}")}
        node.next = -1

    if node.next > 0:
        print(f"{cmd} node {node.manifest['name']}: next {node.next}")
    else:
        print(f"{cmd} node {node.manifest['name']}: completed")

        # fabricのConnectionの場合は、使い終わったら閉じる
        if type(node.c) is Connection:
            node.c.close()

    return {
        "name": node.manifest["name"],
        "result": result,
    }


def _apply(node, cmd=""):
    print(f"{cmd} node {node.manifest['name']}: start {node.next}")
    result = None
    try:
        result = node.apply()
    except Exception as e:
        result = {"status": 1, "msg": colors.crit(f"{str(e)}\n{traceback.format_exc()}")}
        node.next = -1

    if node.next > 0:
        print(f"{cmd} node {node.manifest['name']}: next {node.next}")
    else:
        print(f"{cmd} node {node.manifest['name']}: completed")

        # fabricのConnectionの場合は、使い終わったら閉じる
        if type(node.c) is Connection:
            node.c.close()

    return {
        "name": node.manifest["name"],
        "result": result,
    }


def _delete(node, cmd=""):
    print(f"{cmd} node {node.manifest['name']}: start {node.next}")
    result = None
    try:
        result = node.delete()
    except Exception as e:
        result = {"status": 1, "msg": colors.crit(f"{str(e)}\n{traceback.format_exc()}")}
        node.next = -1

    if node.next > 0:
        print(f"{cmd} node {node.manifest['name']}: next {node.next}")
    else:
        print(f"{cmd} node {node.manifest['name']}: completed")

        # fabricのConnectionの場合は、使い終わったら閉じる
        if type(node.c) is Connection:
            node.c.close()

    return {
        "name": node.manifest["name"],
        "result": result,
    }


def _print_results(results):
    print("# results ----------------------------------------")
    msgs = []
    for name, results in results.items():
        last_result = results[-1]
        last_status = 0
        if last_result is None:
            msgs.append(colors.ok(f"{name}: success"))
        else:
            last_status = last_result.get("status", 0)
            if last_status == 0:
                msgs.append(colors.ok(f"{name}: success"))
            else:
                msgs.append(colors.crit(f"{name}: failed"))

        for result in results:
            if result is not None:
                msgs.append(result.get("msg", ""))
    msg = "\n".join(msgs)
    print(msg)


def _dump_scripts(manifest, cmd, nodes):
    script_path = os.path.join(manifest["_script_dir"], f"{cmd}.sh")
    separator = "#" + "-" * 100
    cmds = []
    for node in nodes:
        cmds += [
            separator,
            f"# {node.manifest['name']} start",
            separator,
        ]
        cmds += node.c.full_cmds
        cmds += [
            separator,
            f"# {node.manifest['name']} end",
            separator,
            "",
        ]

    with open(script_path, "w") as f:
        f.write("\n".join(cmds))
