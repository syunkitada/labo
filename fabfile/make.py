import re
import os
import yaml
from tabulate import tabulate
from invoke.context import Context
from fabric import task, Config, Connection
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict

from lib import colors, spec_utils, os_utils, infra_utils, node_utils


@task
def make(c, file, target="node", cmd="make", debug=False, Dryrun=False, parallel_pool_size=5):
    """make -f [spec_file] -t [kind]:[name_regex] -c [cmd] (-p [parallel_pool_size])

    # target (default=node)
    コマンドの実行対象を限定するために使用します。
    kindは、infra, image, node のいずれかを指定でき、実行対象の種別を限定します。（デフォルトはnodeです）
    [kind]の後ろに、:[name_regex]を指定することで、正規表現により実行対象の名前で限定します。

    # cmd (default=make)
    実行対象のリソースに対するコマンドを指定するために使用します。
    cmdは、make, dump などが指定でき、これはリソースによってサポートされるコマンドが異なります。（デフォルトはmakeです）
    makeは、リソースのスペックに基づいてリソースを実体化するコマンドで、すべてのリソースでサポートされています。

    # debug (default=False)
    実行ログを詳細化します。

    # Dryrun (default=False)
    Dryrunモードで実行します。

    # parallel_pool_size (default=5)
    並列実行のプールサイズです。
    """

    spec = spec_utils.load_spec(file)
    os.makedirs(spec["_script_dir"], exist_ok=True)
    completed_spec_file = os.path.join(spec["_script_dir"], "spec.yaml")
    with open(completed_spec_file, "w") as f:
        f.write(yaml.safe_dump(spec))
    print(f"completed spec was saved to {completed_spec_file}")

    cmds = cmd.split(":")
    if cmd == "dump-spec":
        print(yaml.safe_dump(spec))
        return
    elif cmd == "dump-net":
        _dump_net(spec)
        return

    context_config = {}
    context_config.update(
        {
            "run": {
                "echo": True,
                "echo_format": "{command}",
            },
            "sudo": {
                "echo": True,
                "echo_format": "{command}",
            },
            "local": {
                "echo": True,
                "echo_format": "{command}",
            },
        }
    )
    if os.environ.get("SUDO_USER") is None:
        print("Use sudo")
        exit(1)

    c = _new_runtime_context(context_config, spec)

    if cmd == "dump-netdev":
        netns_map = os_utils.get_netns_map(c)
        _dump_netdev(spec, netns_map)
        return
    elif cmds[0] == "route-trace":
        _trace_route(cmds[1], c, context_config=context_config, spec=spec, debug=debug)
        return

    infra_utils.envrc.cmd(Task(context_config=context_config, cmd=cmd, spec=spec, rspec=None, debug=debug, dryrun=Dryrun))

    re_targets = []
    targets = target.split(":")
    target_kind = targets[0]
    if len(targets) > 1:
        target_strs = targets[1].split(",")
        for t in target_strs:
            re_targets.append(re.compile(t))

    make_infra = False
    make_image = False
    make_node = False
    if target_kind == "all" or target_kind == "infra":
        make_infra = True
    if target_kind == "all" or target_kind == "node":
        make_node = True
    if target_kind == "image":
        make_image = True

    if make_infra:
        for rspec in spec.get("infras", []):
            if _not_target(rspec, re_targets):
                print(f"{cmd} infra {rspec['name']}: skipped")
                continue
            infra_utils.make(Task(context_config=context_config, cmd=cmd, spec=spec, rspec=rspec, debug=debug, dryrun=Dryrun))

    if make_image:
        for name, rspec in spec.get("vm_image_map", {}).items():
            if _not_target(rspec, re_targets):
                print(f"{cmd} image {name}: skipped")
                continue
            node_utils.make_vm_image(Task(context_config=context_config, cmd=cmd, spec=spec, rspec=rspec, debug=debug, dryrun=Dryrun))

    if make_node:
        ctx_data = {
            "netns_map": os_utils.get_netns_map(c),
            "docker_ps_map": infra_utils.docker.get_docker_ps_map(c),
        }

        results = OrderedDict()
        tasks = []
        for rspec in spec.get("nodes", []):
            if _not_target(rspec, re_targets):
                print(f"{cmd} node {rspec['name']}: skipped")
                continue
            tasks.append(
                Task(context_config=context_config, cmd=cmd, spec=spec, rspec=rspec, debug=debug, dryrun=Dryrun, ctx_data=ctx_data)
            )
            results[rspec["name"]] = []

        while True:
            with ThreadPoolExecutor(max_workers=parallel_pool_size) as pool:
                tmp_results = pool.map(node_utils.make, tasks)
            for result in tmp_results:
                results[result["name"]].append(result["result"])

            next_tasks = []
            for t in tasks:
                # nextがインクリメントされた場合はそのタスクを継続します
                if t.next > 0:
                    next_tasks.append(t)
            if len(next_tasks) == 0:
                break
            tasks = next_tasks

        _print_results(results)
        _dump_scripts(spec, cmd, tasks)

        return


class Task:
    def __init__(self, context_config, spec, cmd, rspec, debug, dryrun, ctx_data={}):
        self.c = _new_runtime_context(context_config, spec)
        self.cmd = cmd
        self.spec = spec
        self.rspec = rspec
        self.ctx_data = ctx_data
        self.next = 0
        self.debug = debug
        self.dryrun = dryrun
        self.rc = None


def _new_runtime_context(context_config, spec):
    """
    new_runtime_contextは、ローカルでの実行の場合はinvokeのContextを返し、リモートでの実行の場合はfabricのConnectionを返します。
    fabricはinvokeを利用されて実装されているので、ある程度の互換性を持っており、どちらを利用してるかを意識せずに実装できます。
    """
    common = spec.get("common")
    host = None
    connect_kwargs = {}
    if common is not None:
        host_pass = common.get("host_pass")
        if host_pass is not None:
            context_config["sudo"]["password"] = host_pass
            connect_kwargs["password"] = host_pass
        host_user = common.get("host_user")
        if host_user is not None:
            context_config["user"] = host_user
        host = common.get("host")
    if host is not None:
        c = Connection(host, config=Config(context_config), connect_kwargs=connect_kwargs)
        c.is_local = False
    else:
        c = Context(config=context_config)
        c.is_local = True

    return c


def _not_target(rspec, re_targets):
    if len(re_targets) == 0:
        return False
    name = rspec["name"]
    for r in re_targets:
        if r.match(name):
            return False
    return True


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


def _dump_net(spec):
    topology = []

    def _link_topology(node_topo_index, peer_topo_index, link_name, peer_name):
        link_topo = topology[node_topo_index]
        peer_topo = topology[peer_topo_index]
        for column_index, _ in enumerate(link_topo):
            if link_topo[column_index] is None:
                for row_index in range(node_topo_index, peer_topo_index + 1):
                    if topology[row_index][column_index] is not None:
                        break
                    if row_index == peer_topo_index:
                        # link箇所を埋める
                        link_topo[column_index] = link_name
                        peer_topo[column_index] = "@" + peer_name
                        # linkの間を"|"で埋める
                        for r in range(node_topo_index + 1, peer_topo_index):
                            topology[r][column_index] = "|"
                        return

    node_topo_index_map = {}  # nodeのtopologyの位置
    nodes = spec["nodes"]
    topo_nodes = spec["nodes"]
    topo_width = 20
    # nodesをtopologyに追加
    for i, node in enumerate(nodes):
        topology += [[None] * topo_width]
        node_topo_index_map[node["name"]] = i

    # vmsをtopologyに追加
    topo_index = len(topology)
    for node in nodes:
        for vm in node.get("vms", []):
            topology += [[None] * topo_width]
            topo_nodes.append(vm)
            node_topo_index_map[vm["name"]] = topo_index
            topo_index += 1

    for i, node in enumerate(topo_nodes):
        for link in node.get("links", []):
            _link_topology(i, node_topo_index_map[link["peer"]], link["link_name"], link["peer_name"])
        for link in node.get("vm_links", []):
            _link_topology(i, node_topo_index_map[link["peer"]], link["link_name"], link["peer_name"])

    table_rows = []
    for i, topo in enumerate(topology):
        table_rows.append([topo_nodes[i]["name"]] + topo)
        topo_separator = [""] + [None] * topo_width
        table_rows.append(topo_separator)

    len_table_rows = len(table_rows)
    for i, topo in enumerate(table_rows):
        for j, link in enumerate(topo):
            # linkの開始点ならその下の空いてる部分(None)を"|"で埋める（各node間にtopo_separatorがNodeで挟まってる）
            if link is not None and link != "" and link.split("_")[0] == topo[0]:
                next_index = i + 1
                while next_index < len_table_rows:
                    if table_rows[next_index][j] is None:
                        table_rows[next_index][j] = "|"
                    elif table_rows[next_index][j] != "|":
                        break
                    next_index += 1

    print(tabulate(table_rows, stralign="center", numalign="left", tablefmt="simple"))


def _dump_netdev(spec, netns_map, show_ipv6_link_local=False):
    data = []
    headers = ["node", "netdev"]
    for rspec in spec["nodes"]:
        hostname = rspec["_hostname"]
        if hostname in netns_map:
            netns = netns_map[hostname]
            netdev_infos = []
            for dname, dev in netns["netdev_map"].items():
                netdev_infos.append(f"{dname}: mac={dev.get('mac')}")
                ipv4s = dev.get("inet_map", {}).keys()
                if len(ipv4s) > 0:
                    netdev_infos.append("  ipv4s: " + ",".join(ipv4s))
                ipv6s = []
                for ip in dev.get("inet6_map", {}).keys():
                    if ip.find("fe80:") != 0 or show_ipv6_link_local:
                        ipv6s.append(ip)
                if len(ipv6s) > 0:
                    netdev_infos.append("  ipv6s: " + ",".join(ipv6s))
            data.append([hostname, "\n".join(netdev_infos)])
        else:
            data.append([hostname, "None"])

    print(tabulate(data, headers=headers, stralign="left", numalign="left", tablefmt="fancy_grid"))


def _trace_route(option, c, context_config, spec, debug):
    ctx_data = {
        "netns_map": os_utils.get_netns_map(c),
        "docker_ps_map": infra_utils.docker.get_docker_ps_map(c),
    }
    tasks = []
    for rspec in spec.get("nodes", []):
        tasks.append(Task(context_config=context_config, cmd=None, spec=spec, rspec=rspec, debug=debug, dryrun=False, ctx_data=ctx_data))
    node_utils.trace_route(option, spec, ctx_data, tasks)
    return


def _dump_scripts(spec, cmd, tasks):
    script_path = os.path.join(spec["_script_dir"], f"{cmd}.sh")
    separator = "#" + "-" * 100
    cmds = []
    for t in tasks:
        if t.rc is None:
            continue
        cmds += [
            separator,
            f"# {t.rspec['name']} start",
            separator,
        ]
        cmds += t.rc.full_cmds
        cmds += [
            separator,
            f"# {t.rspec['name']} end",
            separator,
            "",
        ]

    with open(script_path, "w") as f:
        f.write("\n".join(cmds))
