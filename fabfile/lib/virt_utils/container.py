import yaml
import os
from . import context, container_ovs, container_frr


def cmd(cmd, c):
    if cmd == "dump":
        print(yaml.safe_dump(c.rspec))
    elif cmd == "make":
        _make(c)
    elif cmd == "clean":
        _clean(c)


def _clean(c):
    rspec = c.rspec
    if rspec["_hostname"] in c.gctx.docker_ps_map:
        c.gctx.c.sudo(f"docker kill {rspec['_hostname']}")
    if rspec["_hostname"] in c.gctx.netns_map:
        c.gctx.c.sudo(f"rm -rf /var/run/netns/{rspec['_hostname']}")


def _make(c):
    rspec = c.rspec
    os.makedirs(rspec["_script_dir"], exist_ok=True)
    c.gctx.c.sudo(f"rm -rf {rspec['_script_dir']}/*", hide=True)

    dryrun = True
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
    if rspec["_hostname"] not in c.gctx.docker_ps_map:
        dryrun = False
    c.exec(lcmds, title="prepare-docker", dryrun=dryrun, is_local=True)

    dcmds = []
    dcmds += [f"hostname {rspec['_hostname']}"]
    for key, value in rspec.get("sysctl_map", {}).items():
        dcmds += [f"sysctl -w {key}={value}"]
    for bridge in rspec.get("bridges", []):
        dryrun = c.exist_netdev(bridge["name"])
        dcmds += [
            (f"ip link add {bridge['name']} type bridge", dryrun),
            (f"ip link set {bridge['name']} up", dryrun),
            (f"ip link set dev {bridge['name']} mtu {bridge['mtu']}", dryrun),
        ]
        for ip in bridge.get("ips", []):
            c.append_cmds_ip_addr_add(dcmds, ip, bridge["name"])
    c.exec(dcmds, title="init-docker")

    for link in rspec.get("links", []):
        c.append_local_cmds_add_link(lcmds, link)
    for link in rspec.get("_links", []):
        c.append_local_cmds_add_peer(lcmds, link)
    for link in rspec.get("vm_links", []):
        c.append_local_cmds_add_link(lcmds, link)
    c.exec(lcmds, title="prepare-links", is_local=True)

    for link in rspec.get("links", []):
        for vlan_id, _ in link.get("vlan_map", {}).items():
            c.append_cmds_add_vlan(dcmds, link["link_name"], vlan_id)
        if "bridge" in link:
            dcmds += [
                f"ip link set dev {link['link_name']} master {link['bridge']}",
            ]
    for link in rspec.get("_links", []):
        for vlan_id, _ in link.get("vlan_map", {}).items():
            c.append_cmds_add_vlan(dcmds, link["peer_name"], vlan_id)

    for ip in rspec.get("lo_ips", []):
        c.append_cmds_ip_addr_add(dcmds, ip, "lo")
    for link in rspec.get("links", []):
        for ip in link.get("ips", []):
            c.append_cmds_ip_addr_add(dcmds, ip, link["link_name"])
    for link in rspec.get("_links", []):
        for ip in link.get("peer_ips", []):
            c.append_cmds_ip_addr_add(dcmds, ip, link["peer_name"])

    for iprule in rspec.get("ip_rules", []):
        dcmds += [(f"ip rule add {iprule['rule']} prio {iprule['prio']}", c.exist_iprule(iprule["rule"]))]

    for route in rspec.get("routes", []):
        dryrun = c.exist_route(route)
        dcmds += [(f"ip route add {route['dst']} via {route['via']}", dryrun)]
    for route in rspec.get("routes6", []):
        dryrun = c.exist_route6(route)
        dcmds += [(f"ip -6 route add {route['dst']} via {route['via']}", dryrun)]

    c.exec(dcmds, title="setup-networks")

    if "ovs" in rspec:
        container_ovs.make(c)

    if "frr" in rspec:
        container_frr.make(c)

    l3admin = rspec.get("l3admin")
    if l3admin is not None:
        dryrun = c.exist_netdev("l3admin")
        dcmds += [
            ("ip link add l3admin type dummy", dryrun),
            ("ip link set up l3admin", dryrun),
        ]

        iprule = "from all table 300"
        dryrun = c.exist_iprule(iprule)
        dcmds += [(f"ip rule add {iprule} prio 30", dryrun)]

        for ip in l3admin.get("ips", []):
            c.append_cmds_ip_addr_add(dcmds, ip, "l3admin")

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
        c.exec(dcmds, title="setup-l3admin")

    if "cmds" in rspec:
        c.exec(rspec.get("cmds", []), title="cmds")

    for vm in rspec.get("vms", []):
        c = context.ContainerContext(c.gctx, vm)
        _make(c)
