import os

import yaml

from . import container_frr, container_ovs


def make(nctx):
    if nctx.cmd == "dump":
        print(yaml.safe_dump(nctx.rspec))
    elif nctx.cmd == "make" or nctx.cmd == "remake":
        if nctx.next == 0:
            if nctx.cmd == "remake":
                _clean(nctx)
            _make_prepare(nctx)
            nctx.next = 1
        elif nctx.next == 1:
            _make(nctx)
            nctx.next = -1
    elif nctx.cmd == "clean":
        _clean(nctx)
    elif nctx.cmd == "test":
        return nctx.test()


def _clean(nctx):
    rspec = nctx.rspec
    nctx.c.sudo(f"docker kill {rspec['_hostname']}", hide=True, warn=True)
    nctx.c.sudo(f"rm -rf /var/run/netns/{rspec['_hostname']}", hide=True)


def _make_prepare(nctx):
    rspec = nctx.rspec
    os.makedirs(rspec["_script_dir"], exist_ok=True)
    nctx.c.sudo(f"rm -rf {rspec['_script_dir']}/*", hide=True)

    lcmds = []
    for link in rspec.get("links", []):
        nctx.append_local_cmds_add_link(lcmds, link)
    for link in rspec.get("child_links", []):
        nctx.append_local_cmds_add_link(lcmds, link)
    nctx.exec(lcmds, title="prepare-links", is_local=True)

    # メモ: (負荷が高いと？)dockerでsystemdが起動できないことがある
    docker_options = [
        f"-d  --rm --network {rspec.get('network', 'none')} --privileged --cap-add=SYS_ADMIN --name {rspec['_hostname']}",
        "-v /mnt/nfs:/mnt/nfs:ro",
        f"-v {rspec['_script_dir']}:{rspec['_script_dir']}",
    ]

    cgroup = nctx.c.sudo("stat -fc %T /sys/fs/cgroup/").stdout
    if cgroup == "tmpfs":
        docker_options += [
            "-v /sys/fs/cgroup:/sys/fs/cgroup:ro",
        ]
    elif cgroup == "cgroup2fs":
        docker_options += [
            "--cgroup-parent docker.slice",
            "--cgroupns private",
        ]

    for port in rspec.get("ports", []):
        docker_options += [f"-p {port}"]

    lcmds = [
        f"if ! docker inspect {rspec['_hostname']}; then",
        f"docker run {' '.join(docker_options)} {rspec['image']}",
        f"pid=`docker inspect {rspec['_hostname']}" + " --format '{{.State.Pid}}'`",
        "ln -sfT /proc/${pid}/ns/net " + f"/var/run/netns/{rspec['_hostname']}",
        "fi",
    ]
    nctx.exec(lcmds, title="prepare-docker", is_local=True)

    lcmds = []
    for route in rspec.get("local_routes", []):
        lcmds += [
            "ipaddr=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' " + rspec['_hostname'] + ")",
        ]
        nctx.append_cmds_ip_route_add(lcmds, route['dst'], "${ipaddr}")
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
        dcmds += [
            f"if ! ip addr show {bridge['name']}; then",
            f"ip link add {bridge['name']} type bridge",
            f"ip link set {bridge['name']} up",
            f"ip link set dev {bridge['name']} mtu {bridge['mtu']}",
            "fi",
        ]
        for ip in bridge.get("ips", []):
            nctx.append_cmds_ip_addr_add(dcmds, ip, bridge["name"])
    nctx.exec(dcmds, title="init-docker")

    for link in rspec.get("links", []):
        nctx.append_local_cmds_set_link(lcmds, link)
    for link in rspec.get("_links", []):
        nctx.append_local_cmds_set_peer(lcmds, link)
    for link in rspec.get("child_links", []):
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
        dcmds += nctx.wrap_if_exist_iprule(iprule["rule"], [f"ip rule add {iprule['rule']} prio {iprule['prio']}"])

    for route in rspec.get("routes", []):
        nctx.append_cmds_ip_route_add(dcmds, route['dst'], route['via'])
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
        dcmds += nctx.wrap_if_exist_netdev("l3admin", [
            "ip link add l3admin type dummy",
            "ip link set up l3admin",
        ])

        iprule = "from all table 300"
        dcmds += nctx.wrap_if_exist_iprule(iprule, [f"ip rule add {iprule} prio 30"])

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

    if "ansible" in rspec:
        nctx.ansible(rspec['ansible'])
