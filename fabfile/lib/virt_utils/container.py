import yaml
import json
import time
import os


def cmd(cmd, c, spec, rspec):
    if cmd == "dump":
        print(yaml.safe_dump(rspec))
    elif cmd == "make":
        _make(c, spec, rspec)
    elif cmd == "clean":
        _clean(c, spec, rspec)


def _clean(c, spec, rspec):
    if rspec["_hostname"] in c.docker_ps_map:
        c.sudo(f"docker kill {rspec['_hostname']}")
    if rspec["_hostname"] in c.netns_map:
        c.sudo(f"rm -rf /var/run/netns/{rspec['_hostname']}")


def _exec(c, rspec, cmds, title="", dryrun=False, netns=False, docker=False):
    exec_filepath = os.path.join(rspec["_script_dir"], f"{rspec['_script_index']}_{title}_exec.sh")
    full_filepath = os.path.join(rspec["_script_dir"], f"{rspec['_script_index']}_{title}_full.sh")
    rspec["_script_index"] += 1

    exec_cmds = []
    full_cmds = []
    for cmd in cmds:
        if isinstance(cmd, tuple):
            print("cmd", cmd[0], cmd[1], dryrun)
            if not cmd[1] and not dryrun:
                exec_cmds.append(cmd[0])
            full_cmds.append(cmd[0])
        else:
            if not dryrun:
                exec_cmds.append(cmd)
            full_cmds.append(cmd)

    with open(exec_filepath, "w") as f:
        if docker:
            cmds_str = "\n".join(exec_cmds)
            f.write(f"docker exec {rspec['_hostname']} bash -ex -c '\n{cmds_str}'\n")
        elif netns:
            cmds_str = "\n".join(exec_cmds)
            f.write(f"ip netns exec {rspec['_hostname']} bash -ex -c '\n{cmds_str}'\n")
        else:
            f.write("\n".join(exec_cmds))
    if len(exec_cmds) > 0:
        c.sudo(f"bash -ex {exec_filepath}")

    with open(full_filepath, "w") as f:
        if docker:
            cmds_str = "\n".join(full_cmds)
            f.write(f"docker exec {rspec['_hostname']} bash -ex -c '\n{cmds_str}\n'\n")
        elif netns:
            cmds_str = "\n".join(full_cmds)
            f.write(f"ip netns exec {rspec['_hostname']} bash -ex -c '\n{cmds_str}\n'\n")
        else:
            f.write("\n".join(full_cmds))

    cmds.clear()


def _netns_ip_addr_add(c, cmds, rspec, ip, dev):
    if ip["version"] == 4:
        dryrun = True
        if (
            rspec["_hostname"] not in c.netns_map
            or dev not in c.netns_map[rspec["_hostname"]]["netdev_map"]
            or ip["inet"] not in c.netns_map[rspec["_hostname"]]["netdev_map"][dev]["inet_map"]
        ):
            dryrun = False
        cmds += [(f"ip addr add {ip['inet']} dev {dev}", dryrun)]
    elif ip["version"] == 6:
        dryrun = True
        if (
            rspec["_hostname"] not in c.netns_map
            or dev not in c.netns_map[rspec["_hostname"]]["netdev_map"]
            or ip["inet"] not in c.netns_map[rspec["_hostname"]]["netdev_map"][dev]["inet6_map"]
        ):
            dryrun = False
        cmds += [(f"ip addr add {ip['inet']} dev {dev}", dryrun)]


def _netns_ip_route_add(c, cmds, rspec):
    for route in rspec.get("routes", []):
        dryrun = True
        if rspec["_hostname"] not in c.netns_map or route["dst"] not in c.netns_map[rspec["_hostname"]]["route_map"]:
            dryrun = False
        cmds += [(f"ip route add {route['dst']} via {route['via']}", dryrun)]
    for route in rspec.get("routes6", []):
        dryrun = True
        if rspec["_hostname"] not in c.netns_map or route["dst"] not in c.netns_map[rspec["_hostname"]]["route6_map"]:
            dryrun = False
        cmds += [(f"ip -6 route add {route['dst']} via {route['via']}", dryrun)]


def _link(c, cmds, rspec, link, is_peer=False):
    dryrun = True
    if not is_peer:
        if rspec["_hostname"] not in c.netns_map or link["link_name"] not in c.netns_map[rspec["_hostname"]]["netdev_map"]:
            dryrun = False
        cmds += [
            (f"ip link add {link['link_name']} type veth peer name {link['peer_name']}", dryrun),
            (f"ethtool -K {link['link_name']} tso off tx off", dryrun),
            (f"ethtool -K {link['peer_name']} tso off tx off", dryrun),
            (f"ip link set dev {link['link_name']} mtu {link['mtu']}", dryrun),
            (f"ip link set dev {link['link_name']} netns {rspec['_hostname']} up", dryrun),
        ]
    else:
        if rspec["_hostname"] not in c.netns_map or link["peer_name"] not in c.netns_map[rspec["_hostname"]]["netdev_map"]:
            dryrun = False
        cmds += [
            (f"ip link set dev {link['peer_name']} mtu {link['mtu']}", dryrun),
            (f"ip link set dev {link['peer_name']} netns {rspec['_hostname']} up", dryrun),
        ]


def _make(c, spec, rspec):
    os.makedirs(rspec["_script_dir"], exist_ok=True)
    c.sudo(f"rm -rf {rspec['_script_dir']}/*", hide=True)

    dryrun = True
    docker_options = [
        f"-d  --rm --network none --privileged --cap-add=SYS_ADMIN --name {rspec['_hostname']}",
        "-v /sys/fs/cgroup:/sys/fs/cgroup:ro",
        f"-v {rspec['_script_dir']}:{rspec['_script_dir']}",
    ]
    cmds = [
        f"docker run {' '.join(docker_options)} {rspec['image']}",
        f"pid=`docker inspect {rspec['_hostname']}" + " --format '{{.State.Pid}}'`",
        "ln -sfT /proc/${pid}/ns/net " + f"/var/run/netns/{rspec['_hostname']}",
    ]
    if rspec["_hostname"] not in c.docker_ps_map:
        dryrun = False
    _exec(c, rspec, cmds, title="prepare-docker", dryrun=dryrun)

    for key, value in rspec.get("sysctl_map", {}).items():
        cmds += [f"sysctl -w {key}={value}"]
    _exec(c, rspec, cmds, title="docker-sysctl", docker=True)

    for link in rspec.get("links", []):
        _link(c, cmds, rspec, link)
    for link in rspec.get("_links", []):
        _link(c, cmds, rspec, link, is_peer=True)
    _exec(c, rspec, cmds, title="prepare-links")

    ip_add_cmds = []
    for ip in rspec.get("lo_ips", []):
        _netns_ip_addr_add(c, ip_add_cmds, rspec, ip, "lo")
    for link in rspec.get("links", []):
        for ip in link.get("ips", []):
            _netns_ip_addr_add(c, ip_add_cmds, rspec, ip, link["link_name"])
    for link in rspec.get("_links", []):
        for ip in link.get("peer_ips", []):
            _netns_ip_addr_add(c, ip_add_cmds, rspec, ip, link["peer_name"])
    _netns_ip_route_add(c, ip_add_cmds, rspec)
    _exec(c, rspec, ip_add_cmds, title="set-ips", docker=True)

    if "frr" in rspec:
        frr(c, spec, rspec)

    print("script_dir", rspec["_script_dir"])


def frr(c, spec, rspec):
    frr = rspec["frr"]
    daemons = [
        # daemons
        "bgpd=yes",
        "ospfd=no",
        "ospf6d=no",
        "ripd=no",
        "ripngd=no",
        "isisd=no",
        "pimd=no",
        "ldpd=no",
        "nhrpd=no",
        "eigrpd=no",
        "babeld=no",
        "sharpd=no",
        "pbrd=no",
        "bfdd=no",
        "fabricd=no",
        "vrrpd=no",
        "pathd=no",
        # daemon options
        "vtysh_enable=yes",
        'zebra_options="  -A 127.0.0.1 -s 90000000"',
        'bgpd_options="   -A 127.0.0.1"',
        'ospfd_options="  -A 127.0.0.1"',
        'ospf6d_options=" -A ::1"',
        'ripd_options="   -A 127.0.0.1"',
        'ripngd_options=" -A ::1"',
        'isisd_options="  -A 127.0.0.1"',
        'pimd_options="   -A 127.0.0.1"',
        'ldpd_options="   -A 127.0.0.1"',
        'nhrpd_options="  -A 127.0.0.1"',
        'eigrpd_options=" -A 127.0.0.1"',
        'babeld_options=" -A 127.0.0.1"',
        'sharpd_options=" -A 127.0.0.1"',
        'pbrd_options="   -A 127.0.0.1"',
        'staticd_options="-A 127.0.0.1"',
        'bfdd_options="   -A 127.0.0.1"',
        'fabricd_options="-A 127.0.0.1"',
        'vrrpd_options="  -A 127.0.0.1"',
        'pathd_options="  -A 127.0.0.1"',
    ]
    frr_daemons_txt = "\n".join(daemons).replace('"', '\\"')
    cmds = [
        f'txt="{frr_daemons_txt}"',
        'echo "$txt" > /etc/frr/daemons',
        "sed -i 's/StartLimitInterval=.*/StartLimitInterval=10s/' /usr/lib/systemd/system/frr.service",
        "systemctl daemon-reload",
        "systemctl restart frr",
    ]
    _exec(c, rspec, cmds, title="frr_daemons", docker=True)

    vtysh_cmds = [
        "configure terminal",
        f"hostname {rspec['_hostname']}",
        "log file /var/log/frr/frr.log",
        "!",
    ]

    # setup interfaces
    for link in rspec.get("links", []):
        if "bgp_peer_group" in link:
            vtysh_cmds += [
                f"interface {link['link_name']}",
                "ipv6 nd ra-interval 10",
                "no ipv6 nd suppress-ra",
                "!",
            ]
    for link in rspec.get("_links", []):
        if "bgp_peer_group" in link:
            vtysh_cmds += [
                f"interface {link['peer_name']}",
                "ipv6 nd ra-interval 10",
                "no ipv6 nd suppress-ra",
                "!",
            ]

    # seup bgp
    vtysh_cmds += [
        f"router bgp {frr['asn']}",
    ]

    for bgp_peer_group in frr.get("bgp_peer_groups", []):
        vtysh_cmds += [
            f"neighbor {bgp_peer_group['name']} peer-group",
            f"neighbor {bgp_peer_group['name']} remote-as external",
            f"neighbor {bgp_peer_group['name']} capability extended-nexthop",
        ]
    for link in rspec.get("links", []):
        if "bgp_peer_group" in link:
            vtysh_cmds += [f"neighbor {link['link_name']} interface peer-group {link['bgp_peer_group']}"]
    for link in rspec.get("_links", []):
        if "bgp_peer_group" in link:
            vtysh_cmds += [f"neighbor {link['peer_name']} interface peer-group {link['bgp_peer_group']}"]

    vtysh_cmds += ["address-family ipv4 unicast"]
    for network in frr.get("ipv4_networks", []):
        vtysh_cmds += [f"network {network}"]
    vtysh_cmds += ["exit-address-family"]

    vtysh_cmds += ["address-family ipv6 unicast"]
    for network in frr.get("ipv6_networks", []):
        vtysh_cmds += [f"network {network}"]
    vtysh_cmds += ["exit-address-family"]

    vtysh_cmds += [
        "exit",
    ]
    vtysh_cmds_str = "\n".join(vtysh_cmds)
    cmds = [f'vtysh -c "{vtysh_cmds_str}"']
    _exec(c, rspec, cmds, title="frr_vtysh", docker=True)
