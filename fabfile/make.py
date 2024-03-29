import os
import re
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

import yaml
from invoke import context as invoke
import fabric
from lib import colors, node_utils, os_utils, spec_utils, task_utils
from node import node_context, node_manager
from lib.runtime import runtime_context
from tabulate import tabulate


@fabric.task
def make(c, file, target="", cmd="make", debug=False, Dryrun=False, parallel_pool_size=5):
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
    if cmds[0] == "dump-spec":
        print(yaml.safe_dump(spec))
        return
    elif cmds[0] == "dump-net":
        _dump_net(spec)
        return
    elif cmds[0] == "dump-vm":
        _dump_vm(spec)
        return

    c = runtime_context.new(spec)

    if cmd == "dump-netdev":
        netns_map = os_utils.get_netns_map(c)
        _dump_netdev(spec, netns_map)
        return

    re_targets = task_utils.target.get_re_targets(target)

    results = OrderedDict()
    node_ctxs = []
    def init_node_ctx(rspec):
        if not task_utils.target.is_target(rspec, re_targets):
            return
        node_ctxs.append(
            node_context.NodeContext(cmd=cmd, spec=spec, rspec=rspec, debug=debug, dryrun=Dryrun)
        )
        results[rspec["name"]] = []

        for child in rspec.get("childs", []):
            init_node_ctx(child)

    for rspec in spec.get("nodes", []):
        init_node_ctx(rspec)

    if not Dryrun and cmd == "make":
        spec_utils.check_requrements(c, node_ctxs)

    while True:
        with ThreadPoolExecutor(max_workers=parallel_pool_size) as pool:
            tmp_results = pool.map(node_manager.make, node_ctxs)
        for result in tmp_results:
            results[result["name"]].append(result["result"])

        next_node_ctxs = []
        for t in node_ctxs:
            # nextがインクリメントされたnode_ctxsのみ次のタスクを実行します
            if t.next > 0:
                next_node_ctxs.append(t)
        if len(next_node_ctxs) == 0:
            break
        node_ctxs = next_node_ctxs

    _print_results(results)
    _dump_scripts(spec, cmd, node_ctxs)

    return


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
        for vm in node.get("childs", []):
            topology += [[None] * topo_width]
            topo_nodes.append(vm)
            node_topo_index_map[vm["name"]] = topo_index
            topo_index += 1

    for i, node in enumerate(topo_nodes):
        for link in node.get("links", []):
            _link_topology(i, node_topo_index_map[link["peer"]], link["link_name"], link["peer_name"])
        for link in node.get("child_links", []):
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


def _dump_vm(spec):
    print("# vips ----------------------------------------")
    headers = ["vpc_id", "vip", "vip", "members"]
    table_rows = []
    for key, vip in spec.get("vip_map", {}).items():
        members = []
        for member in vip["members"]:
            for _link in member["_node"]["_links"]:
                for ip in _link["peer_ips"]:
                    members.append(f"{member['name']} {ip['ip']}")
        table_rows.append([vip["vpc_id"], key, vip["vip"]["ip"], "\n".join(members)])
    print(tabulate(table_rows, headers=headers, stralign="center", numalign="left", tablefmt="simple"))

    print("\n# vms ----------------------------------------")
    headers = ["hv", "vpc_id", "vm", "ips"]
    table_rows = []
    for node in spec.get("nodes", []):
        for vm in node.get("vms", []):
            ips = []
            for _link in vm.get("_links", []):
                for ip in _link.get("peer_ips", []):
                    ips.append(ip["ip"])
            table_rows.append([node["name"], vm.get("vpc_id"), vm["name"], ",".join(ips)])
    print(tabulate(table_rows, headers=headers, stralign="center", numalign="left", tablefmt="simple"))


# def _trace_route(option, c, context_config, spec, debug):
#     ctx_data = {
#         "netns_map": os_utils.get_netns_map(c),
#         "docker_ps_map": infra_utils.docker.get_docker_ps_map(c),
#     }
#     options = option.split("_")
#     srcs = options[0].split(".")
#     dsts = options[1].split(".")
#     src_node = spec["_node_map"][srcs[0]]
#     dst_node = spec["_node_map"][dsts[0]]
#     src_ip = None
#     dst_ip = None
# 
#     for link in src_node.get("links", []):
#         for ip in link.get("ips", []):
#             src_ip = ip
#             break
#         if src_ip is not None:
#             break
#     if src_ip is None:
#         for link in src_node.get("_links", []):
#             for ip in link.get("peer_ips", []):
#                 src_ip = ip
#                 break
#             if src_ip is not None:
#                 break
# 
#     for link in dst_node.get("links", []):
#         for ip in link.get("ips", []):
#             dst_ip = ip
#             break
#         if dst_ip is not None:
#             break
#     if dst_ip is None:
#         for link in dst_node.get("_links", []):
#             for ip in link.get("peer_ips", []):
#                 dst_ip = ip
#                 break
#             if dst_ip is not None:
#                 break
# 
#     task = NodeContext(context_config=context_config, cmd=None, spec=spec, rspec=src_node, debug=debug, dryrun=False, ctx_data=ctx_data)
#     src = {
#         "node": src_node,
#         "ip": src_ip,
#     }
#     dst = {
#         "node": dst_node,
#         "ip": dst_ip,
#     }
#     node_utils.trace_route(task, src, dst)
#     return


def _dump_scripts(spec, cmd, nodes):
    script_path = os.path.join(spec["_script_dir"], f"{cmd}.sh")
    separator = "#" + "-" * 100
    cmds = []
    for nctx in nodes:
        cmds += [
            separator,
            f"# {nctx.rspec['name']} start",
            separator,
        ]
        cmds += nctx.full_cmds
        cmds += [
            separator,
            f"# {nctx.rspec['name']} end",
            separator,
            "",
        ]

    with open(script_path, "w") as f:
        f.write("\n".join(cmds))
