import yaml
import os
from . import container_ovs, container_frr
from lib import colors


def cmd(t):
    if t.cmd == "dump":
        print(yaml.safe_dump(t.rspec))
    elif t.cmd == "make":
        if t.next == 0:
            _make_prepare(t.rc)
            t.next = 1
        elif t.next == 1:
            _make(t.rc)
            t.next = -1
    elif t.cmd == "remake":
        if t.next == 0:
            _clean(t.rc)
            _make_prepare(t.rc)
            t.next = 1
        elif t.next == 1:
            _make(t.rc)
            t.next = -1
    elif t.cmd == "clean":
        _clean(t.rc)
    elif t.cmd == "test":
        return _test(t.rc)


def _clean(rc):
    rspec = rc.rspec
    if rspec["_hostname"] in rc.docker_ps_map:
        rc.c.sudo(f"docker kill {rspec['_hostname']}", hide=True)
    if rspec["_hostname"] in rc.netns_map:
        rc.c.sudo(f"rm -rf /var/run/netns/{rspec['_hostname']}", hide=True)

    for vm in rspec.get("vms", []):
        rc.rspec = vm
        _clean(rc)


def _test(rc):
    rspec = rc.rspec
    status = 0
    msgs = []
    ok_targets = []
    ng_targets = []
    for test in rspec.get("tests", []):
        if test["kind"] == "ping":
            for target in test["targets"]:
                err = _ping(rc, target)
                if err is None:
                    ok_targets.append(target)
                else:
                    status += 1
                    target["err"] = err
                    ng_targets.append(target)
    if len(ok_targets) > 0:
        ok_msgs = ["ok_results"]
        for target in ok_targets:
            ok_msgs.append(f"{rspec['name']} ping to {target['name']}(dst={target['dst']})")
        msgs.append(colors.ok("\n".join(ok_msgs)))
    if len(ng_targets) > 0:
        ng_msgs = ["ng_results"]
        for target in ng_targets:
            ng_msgs.append(f"{rspec['name']} ping to {target['name']}(dst={target['dst']},err={target['err']})")
        msgs.append(colors.crit("\n".join(ng_msgs)))

    for vm in rspec.get("vms", []):
        rc.rspec = vm
        result = _test(rc)
        status += result["status"]
        msgs.append(result["msg"])

    msgs.append("")
    return {
        "status": status,
        "msg": "\n".join(msgs),
    }


def _ping(rc, target):
    result = rc.dexec(f"ping -c 1 -W 1 {target['dst']}", hide=True, warn=True)
    if result.return_code == 0:
        return
    else:
        return result.stdout + result.stderr


def _make_prepare(rc):
    rspec = rc.rspec
    os.makedirs(rspec["_script_dir"], exist_ok=True)
    rc.c.sudo(f"rm -rf {rspec['_script_dir']}/*", hide=True)

    lcmds = []
    for link in rspec.get("links", []):
        rc.append_local_cmds_add_link(lcmds, link)
    for link in rspec.get("vm_links", []):
        rc.append_local_cmds_add_link(lcmds, link)
    rc.exec(lcmds, title="prepare-links", is_local=True)

    # メモ: (負荷が高いと？)dockerでsystemdが起動できないことがある
    docker_options = [
        f"-d  --rm --network none --privileged --cap-add=SYS_ADMIN --name {rspec['_hostname']}",
        "-v /sys/fs/cgroup:/sys/fs/cgroup:ro",
        f"-v {rspec['_script_dir']}:{rspec['_script_dir']}",
    ]
    lcmds = [
        f"docker run {' '.join(docker_options)} {rspec['image']}",
        f"pid=`docker inspect {rspec['_hostname']}" + " --format '{{.State.Pid}}'`",
        "ln -sfT /proc/${pid}/ns/net " + f"/var/run/netns/{rspec['_hostname']}",
    ]
    rc.exec(lcmds, title="prepare-docker", skipped=(rspec["_hostname"] in rc.docker_ps_map), is_local=True)


def _make(rc):
    rspec = rc.rspec

    skipped = False

    lcmds = []
    dcmds = []
    dcmds += [f"hostname {rspec['_hostname']}"]
    for key, value in rspec.get("sysctl_map", {}).items():
        dcmds += [f"sysctl -w {key}={value}"]
    for bridge in rspec.get("bridges", []):
        skipped = rc.exist_netdev(bridge["name"])
        dcmds += [
            (f"ip link add {bridge['name']} type bridge", skipped),
            (f"ip link set {bridge['name']} up", skipped),
            (f"ip link set dev {bridge['name']} mtu {bridge['mtu']}", skipped),
        ]
        for ip in bridge.get("ips", []):
            rc.append_cmds_ip_addr_add(dcmds, ip, bridge["name"])
    rc.exec(dcmds, title="init-docker")

    for link in rspec.get("links", []):
        rc.append_local_cmds_set_link(lcmds, link)
    for link in rspec.get("_links", []):
        rc.append_local_cmds_set_peer(lcmds, link)
    for link in rspec.get("vm_links", []):
        rc.append_local_cmds_set_link(lcmds, link)
    rc.exec(lcmds, title="prepare-links", is_local=True)

    for link in rspec.get("links", []):
        for vlan_id, _ in link.get("vlan_map", {}).items():
            rc.append_cmds_add_vlan(dcmds, link["link_name"], vlan_id)
        if "bridge" in link:
            dcmds += [
                f"ip link set dev {link['link_name']} master {link['bridge']}",
            ]
    for link in rspec.get("_links", []):
        for vlan_id, _ in link.get("vlan_map", {}).items():
            rc.append_cmds_add_vlan(dcmds, link["peer_name"], vlan_id)

    for ip in rspec.get("lo_ips", []):
        rc.append_cmds_ip_addr_add(dcmds, ip, "lo")
    for link in rspec.get("links", []):
        for ip in link.get("ips", []):
            rc.append_cmds_ip_addr_add(dcmds, ip, link["link_name"])
    for link in rspec.get("_links", []):
        for ip in link.get("peer_ips", []):
            rc.append_cmds_ip_addr_add(dcmds, ip, link["peer_name"])

    for iprule in rspec.get("ip_rules", []):
        dcmds += [(f"ip rule add {iprule['rule']} prio {iprule['prio']}", rc.exist_iprule(iprule["rule"]))]

    for route in rspec.get("routes", []):
        skipped = rc.exist_route(route)
        dcmds += [(f"ip route add {route['dst']} via {route['via']}", skipped)]
    for route in rspec.get("routes6", []):
        skipped = rc.exist_route6(route)
        dcmds += [(f"ip -6 route add {route['dst']} via {route['via']}", skipped)]

    rc.exec(dcmds, title="setup-networks")

    if "ovs" in rspec:
        container_ovs.make(rc)

    if "frr" in rspec:
        container_frr.make(rc)

    l3admin = rspec.get("l3admin")
    if l3admin is not None:
        skipped = rc.exist_netdev("l3admin")
        dcmds += [
            ("ip link add l3admin type dummy", skipped),
            ("ip link set up l3admin", skipped),
        ]

        iprule = "from all table 300"
        skipped = rc.exist_iprule(iprule)
        dcmds += [(f"ip rule add {iprule} prio 30", skipped)]

        for ip in l3admin.get("ips", []):
            rc.append_cmds_ip_addr_add(dcmds, ip, "l3admin")

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
        rc.exec(dcmds, title="setup-l3admin")

    if "cmds" in rspec:
        rc.exec(rspec.get("cmds", []), title="cmds")

    for vm in rspec.get("vms", []):
        rc.rspec = vm
        _make_prepare(rc)
        _make(rc)
