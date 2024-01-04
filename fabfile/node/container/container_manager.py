import os

import yaml
from lib import colors

from . import container_frr, container_ovs


def make(nctx):
    if nctx.cmd == "dump":
        print(yaml.safe_dump(nctx.rspec))
    elif nctx.cmd == "make":
        if nctx.next == 0:
            _make_prepare(nctx)
            nctx.next = 1
        elif nctx.next == 1:
            _make(nctx)
            nctx.next = -1
    elif nctx.cmd == "remake":
        if nctx.next == 0:
            _clean(nctx)
            _make_prepare(nctx)
            nctx.next = 1
        elif nctx.next == 1:
            _make(nctx)
            nctx.next = -1
    elif nctx.cmd == "clean":
        _clean(nctx)
    elif nctx.cmd == "test":
        return _test(nctx)


def _clean(nctx):
    rspec = nctx.rspec
    if rspec["_hostname"] in nctx.docker_ps_map:
        nctx.c.sudo(f"docker kill {rspec['_hostname']}", hide=True)
    if rspec["_hostname"] in nctx.netns_map:
        nctx.c.sudo(f"rm -rf /var/run/netns/{rspec['_hostname']}", hide=True)

    for vm in rspec.get("vms", []):
        nctx.rspec = vm
        _clean(nctx)


def _test(nctx):
    rspec = nctx.rspec
    status = 0
    msgs = []
    ok_msgs = []
    ng_msgs = []
    for test in rspec.get("tests", []):
        msg = ""
        err = None
        if test["kind"] == "ping":
            for target in test["targets"]:
                msg, err = _ping(rc, target)
        elif test["kind"] == "cmd":
            if "cmd" in test:
                msg, err = _cmd(rc, test["cmd"])
        if err is None:
            ok_msgs.append(f"{test['kind']}: {msg}")
        else:
            status += 1
            ng_msgs.append(f"{test['kind']}: {msg}\nerr={err}")

    if len(ok_msgs) > 0:
        ok_msgs.insert(0, "ok_results")
        msgs.append(colors.ok("\n".join(ok_msgs)))
    if len(ng_msgs) > 0:
        ng_msgs.insert(0, "ng_results")
        msgs.append(colors.crit("\n".join(ng_msgs)))

    for vm in rspec.get("vms", []):
        nctx.rspec = vm
        result = _test(rc)
        status += result["status"]
        msgs.append(result["msg"])

    msgs.append("")
    return {
        "status": status,
        "msg": "\n".join(msgs),
    }


def _ping(nctx, target):
    result = nctx.dexec(f"ping -c 1 -W 1 {target['dst']}", hide=True, warn=True)
    msg = f"{nctx.rspec['name']}: ping to {target['name']}(dst={target['dst']})"
    if result.return_code == 0:
        return msg, None
    else:
        return msg, result.stdout + result.stderr


def _cmd(nctx, cmd):
    msg = f"{nctx.rspec['name']}: {cmd}"
    result = nctx.dexec(cmd, hide=True, warn=True)
    if result.return_code == 0:
        return msg, None
    else:
        return msg, result.stdout + result.stderr


def _make_prepare(nctx):
    rspec = nctx.rspec
    os.makedirs(rspec["_script_dir"], exist_ok=True)
    nctx.c.sudo(f"rm -rf {rspec['_script_dir']}/*", hide=True)

    lcmds = []
    for link in rspec.get("links", []):
        nctx.append_local_cmds_add_link(lcmds, link)
    for link in rspec.get("vm_links", []):
        nctx.append_local_cmds_add_link(lcmds, link)
    nctx.exec(lcmds, title="prepare-links", is_local=True)

    # メモ: (負荷が高いと？)dockerでsystemdが起動できないことがある
    docker_options = [
        f"-d  --rm --network {rspec.get('network', 'none')} --privileged --cap-add=SYS_ADMIN --name {rspec['_hostname']}",
        "-v /sys/fs/cgroup:/sys/fs/cgroup:ro",
        f"-v {rspec['_script_dir']}:{rspec['_script_dir']}",
    ]
    lcmds = [
        f"docker run {' '.join(docker_options)} {rspec['image']}",
        f"pid=`docker inspect {rspec['_hostname']}" + " --format '{{.State.Pid}}'`",
        "ln -sfT /proc/${pid}/ns/net " + f"/var/run/netns/{rspec['_hostname']}",
    ]
    nctx.exec(lcmds, title="prepare-docker", skipped=(rspec["_hostname"] in nctx.docker_ps_map), is_local=True)

    lcmds = []
    for route in rspec.get("local_routes", []):
        lcmds += [
            "ipaddr=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' " + rspec['_hostname'] + ")",
            "ip route | grep \"" + route['dst'] + " via ${ipaddr}\" || ip route add " + route['dst'] + " via ${ipaddr}",
        ]
    nctx.exec(lcmds, title="local_routes", is_local=True)

def _make(nctx):
    rspec = nctx.rspec

    skipped = False

    lcmds = []
    dcmds = []
    dcmds += [f"hostname {rspec['_hostname']}"]
    for key, value in rspec.get("sysctl_map", {}).items():
        dcmds += [f"sysctl -w {key}={value}"]
    for bridge in rspec.get("bridges", []):
        skipped = nctx.exist_netdev(bridge["name"])
        dcmds += [
            (f"ip link add {bridge['name']} type bridge", skipped),
            (f"ip link set {bridge['name']} up", skipped),
            (f"ip link set dev {bridge['name']} mtu {bridge['mtu']}", skipped),
        ]
        for ip in bridge.get("ips", []):
            nctx.append_cmds_ip_addr_add(dcmds, ip, bridge["name"])
    nctx.exec(dcmds, title="init-docker")

    for link in rspec.get("links", []):
        nctx.append_local_cmds_set_link(lcmds, link)
    for link in rspec.get("_links", []):
        nctx.append_local_cmds_set_peer(lcmds, link)
    for link in rspec.get("vm_links", []):
        nctx.append_local_cmds_set_link(lcmds, link)
    nctx.exec(lcmds, title="prepare-links", is_local=True)

    for link in rspec.get("links", []):
        for vlan_id, _ in link.get("vlan_map", {}).items():
            nctx.append_cmds_add_vlan(dcmds, link["link_name"], vlan_id)
        if "bridge" in link:
            dcmds += [
                f"ip link set dev {link['link_name']} master {link['bridge']}",
            ]
    for link in rspec.get("_links", []):
        for vlan_id, _ in link.get("vlan_map", {}).items():
            nctx.append_cmds_add_vlan(dcmds, link["peer_name"], vlan_id)

    for ip in rspec.get("lo_ips", []):
        nctx.append_cmds_ip_addr_add(dcmds, ip, "lo")
    for link in rspec.get("links", []):
        for ip in link.get("ips", []):
            nctx.append_cmds_ip_addr_add(dcmds, ip, link["link_name"])
    for link in rspec.get("_links", []):
        for ip in link.get("peer_ips", []):
            nctx.append_cmds_ip_addr_add(dcmds, ip, link["peer_name"])
    if "sid" in rspec:
        nctx.append_cmds_ip_addr_add(dcmds, rspec["sid"], rspec["sid"]["dev"])

    for iprule in rspec.get("ip_rules", []):
        dcmds += [(f"ip rule add {iprule['rule']} prio {iprule['prio']}", nctx.exist_iprule(iprule["rule"]))]

    for route in rspec.get("routes", []):
        skipped = nctx.exist_route(route)
        dcmds += [(f"ip route add {route['dst']} via {route['via']}", skipped)]
    for route in rspec.get("routes6", []):
        skipped = nctx.exist_route6(route)
        dcmds += [(f"ip -6 route add {route['dst']} via {route['via']}", skipped)]

    nctx.exec(dcmds, title="setup-networks")

    if "ovs" in rspec:
        container_ovs.make(nctx)

    if "frr" in rspec:
        container_frr.make(nctx)

    l3admin = rspec.get("l3admin")
    if l3admin is not None:
        skipped = nctx.exist_netdev("l3admin")
        dcmds += [
            ("ip link add l3admin type dummy", skipped),
            ("ip link set up l3admin", skipped),
        ]

        iprule = "from all table 300"
        skipped = nctx.exist_iprule(iprule)
        dcmds += [(f"ip rule add {iprule} prio 30", skipped)]

        for ip in l3admin.get("ips", []):
            nctx.append_cmds_ip_addr_add(dcmds, ip, "l3admin")

        routes = []
        for link in rspec.get("_links", []):
            for vlan_id, vlan in link.get("vlan_map", {}).items():
                if vlan.get("bgp_peer_group", "") == "ADMIN":
                    dcmds += [
                        # frrが以下の設定を入れてくれるので、169.254.0.1をgatewayとして使える
                        # 169.254.0.1 dev HV1_0_L11.100 lladdr 5e:de:b2:b4:98:4f PERMANENT proto zebra
                        # ルートを設定するために、仮で169.254.0.2/24を各インターフェイスに付ける
                        f"ip addr show {link['peer_name']}.{vlan_id} | grep 169.254.0.2/24"
                        + f" || ip addr add 169.254.0.2/24 dev {link['peer_name']}.{vlan_id}",
                    ]
                    routes += [f"nexthop via 169.254.0.1 dev {link['peer_name']}.{vlan_id}"]
        if len(routes) > 0:
            for ip in l3admin.get("ips", []):
                if ip["version"] == 4:
                    dcmds += [f"ip route replace table 300 0.0.0.0/0 src {ip['ip']} {' '.join(routes)}"]
        nctx.exec(dcmds, title="setup-l3admin")

    if "cmds" in rspec:
        nctx.exec(rspec.get("cmds", []), title="cmds")

    for child in nctx.childs:
        _make(child)
    # for vm in rspec.get("vms", []):
    #     nctx.rspec = vm
    #     _make_prepare(rc)
    #     _make(rc)
