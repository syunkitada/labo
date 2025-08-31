import os
import logging
from fabric import Connection
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
import traceback

from mylabo.domain import resource
from mylabo.lib.resource_controller.container import container
from mylabo.lib.resource_controller.vm import vm
from mylabo.lib import colors
from mylabo.lib.runtime import runtime_context

LOG = logging.getLogger(__name__)


class Infra(resource.Resource):
    def __init__(self, spec):
        self.spec = spec
        self.c = runtime_context.new(spec)
        self.next = 0
        self.parallel_pool_size = 1  # TODO : Make this configurable

    def get(self, labels: dict):
        results = []
        for node_spec in self.spec["spec"].get("nodes", []):
            node_spec["_root_spec"] = self.spec
            if node_spec["kind"] == "vm":
                node = vm.VM(node_spec)
            elif node_spec["kind"] == "container":
                node = container.Container(node_spec)
            else:
                raise ValueError(f"Unsupported node kind: {node_spec['kind']}")

            results.append(node.get(labels))

        return results

    def _init_nodes(self, spec, labels: dict):
        results = OrderedDict()
        nodes = []

        def _init(spec):
            for node_spec in spec["spec"].get("nodes", []):
                label_name = labels.get("name")
                if label_name is not None and node_spec["name"] != label_name:
                    continue

                node_spec["_root_spec"] = self.spec
                if node_spec["kind"] == "vm":
                    node = vm.VM(node_spec)
                elif node_spec["kind"] == "container":
                    node = container.Container(node_spec)
                else:
                    raise ValueError(f"Unsupported node kind: {node_spec['kind']}")

                results[node_spec["name"]] = []
                nodes.append(node)

                _init(node_spec)

        _init(spec)

        return nodes, results

    def apply(self, labels: dict):
        print("apply", self.spec)

        nodes, results = self._init_nodes(self.spec, labels)

        os.makedirs(self.spec["_script_dir"], exist_ok=True)
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
        _dump_scripts(self.spec, "apply", nodes)

    def delete(self, labels: dict):
        nodes, results = self._init_nodes(self.spec, labels)

        os.makedirs(self.spec["_script_dir"], exist_ok=True)
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
        _dump_scripts(self.spec, "apply", nodes)

    def test(self, labels: dict):
        print("test", self.spec)

        nodes, results = self._init_nodes(self.spec, labels)

        os.makedirs(self.spec["_script_dir"], exist_ok=True)
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
        _dump_scripts(self.spec, "test", nodes)


def _test(node, cmd=""):
    print(f"{cmd} node {node.spec['name']}: start {node.next}")
    result = None
    try:
        result = node.test()
    except Exception as e:
        result = {"status": 1, "msg": colors.crit(f"{str(e)}\n{traceback.format_exc()}")}
        node.next = -1

    if node.next > 0:
        print(f"{cmd} node {node.spec['name']}: next {node.next}")
    else:
        print(f"{cmd} node {node.spec['name']}: completed")

        # fabricのConnectionの場合は、使い終わったら閉じる
        if type(node.c) is Connection:
            node.c.close()

    return {
        "name": node.spec["name"],
        "result": result,
    }


def _apply(node, cmd=""):
    print(f"{cmd} node {node.spec['name']}: start {node.next}")
    result = None
    try:
        result = node.apply()
    except Exception as e:
        result = {"status": 1, "msg": colors.crit(f"{str(e)}\n{traceback.format_exc()}")}
        node.next = -1

    if node.next > 0:
        print(f"{cmd} node {node.spec['name']}: next {node.next}")
    else:
        print(f"{cmd} node {node.spec['name']}: completed")

        # fabricのConnectionの場合は、使い終わったら閉じる
        if type(node.c) is Connection:
            node.c.close()

    return {
        "name": node.spec["name"],
        "result": result,
    }


def _delete(node, cmd=""):
    print(f"{cmd} node {node.spec['name']}: start {node.next}")
    result = None
    try:
        result = node.delete()
    except Exception as e:
        result = {"status": 1, "msg": colors.crit(f"{str(e)}\n{traceback.format_exc()}")}
        node.next = -1

    if node.next > 0:
        print(f"{cmd} node {node.spec['name']}: next {node.next}")
    else:
        print(f"{cmd} node {node.spec['name']}: completed")

        # fabricのConnectionの場合は、使い終わったら閉じる
        if type(node.c) is Connection:
            node.c.close()

    return {
        "name": node.spec["name"],
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


def _dump_scripts(spec, cmd, nodes):
    script_path = os.path.join(spec["_script_dir"], f"{cmd}.sh")
    separator = "#" + "-" * 100
    cmds = []
    for node in nodes:
        cmds += [
            separator,
            f"# {node.spec['name']} start",
            separator,
        ]
        cmds += node.c.full_cmds
        cmds += [
            separator,
            f"# {node.spec['name']} end",
            separator,
            "",
        ]

    with open(script_path, "w") as f:
        f.write("\n".join(cmds))
