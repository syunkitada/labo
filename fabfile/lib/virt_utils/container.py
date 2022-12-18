import yaml
import os
from . import context


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


def append_cmds_ip_addr_add(c, cmds, ip, dev):
    if ip["version"] == 4:
        dryrun = c.exist_netdev(dev) and ip["inet"] in c.gctx.netns_map[c.rspec["_hostname"]]["netdev_map"][dev]["inet_map"]
        cmds += [(f"ip addr add {ip['inet']} dev {dev}", dryrun)]
    elif ip["version"] == 6:
        dryrun = c.exist_netdev(dev) and ip["inet"] in c.gctx.netns_map[c.rspec["_hostname"]]["netdev_map"][dev]["inet6_map"]
        cmds += [(f"ip addr add {ip['inet']} dev {dev}", dryrun)]


def append_local_cmds_add_link(c, cmds, link):
    dryrun = c.exist_netdev(link["link_name"])
    cmds += [
        (f"ip link add {link['link_name']} type veth peer name {link['peer_name']}", dryrun),
        (f"ethtool -K {link['link_name']} tso off tx off", dryrun),
        (f"ip link set dev {link['link_name']} mtu {link['mtu']}", dryrun),
        (f"ip link set dev {link['link_name']} netns {c.rspec['_hostname']} up", dryrun),
    ]


def append_local_cmds_add_peer(c, cmds, link):
    dryrun = c.exist_netdev(link["peer_name"])
    cmds += [
        (f"ethtool -K {link['peer_name']} tso off tx off", dryrun),
        (f"ip link set dev {link['peer_name']} mtu {link['mtu']}", dryrun),
        (f"ip link set dev {link['peer_name']} netns {c.rspec['_hostname']} up", dryrun),
    ]


def append_cmds_add_vlan(c, cmds, netdev, vlan_id):
    netdev_vlan = f"{netdev}.{vlan_id}"
    dryrun = c.exist_netdev(netdev_vlan)
    cmds += [
        (f"ip link add link {netdev} name {netdev_vlan} type vlan id {vlan_id}", dryrun),
        (f"ip link set {netdev_vlan} up", dryrun),
    ]


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
            append_cmds_ip_addr_add(c, dcmds, ip, bridge["name"])
    c.exec(dcmds, title="init-docker")

    for link in rspec.get("links", []):
        append_local_cmds_add_link(c, lcmds, link)
    for link in rspec.get("_links", []):
        append_local_cmds_add_peer(c, lcmds, link)
    for link in rspec.get("vm_links", []):
        append_local_cmds_add_link(c, lcmds, link)
    c.exec(lcmds, title="prepare-links", is_local=True)

    for link in rspec.get("links", []):
        for vlan_id, _ in link.get("vlan_map", {}).items():
            append_cmds_add_vlan(c, dcmds, link["link_name"], vlan_id)
        if "bridge" in link:
            dcmds += [
                f"ip link set dev {link['link_name']} master {link['bridge']}",
            ]
    for link in rspec.get("_links", []):
        for vlan_id, _ in link.get("vlan_map", {}).items():
            append_cmds_add_vlan(c, dcmds, link["peer_name"], vlan_id)

    for ip in rspec.get("lo_ips", []):
        append_cmds_ip_addr_add(c, dcmds, ip, "lo")
    for link in rspec.get("links", []):
        for ip in link.get("ips", []):
            append_cmds_ip_addr_add(c, dcmds, ip, link["link_name"])
    for link in rspec.get("_links", []):
        for ip in link.get("peer_ips", []):
            append_cmds_ip_addr_add(c, dcmds, ip, link["peer_name"])

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
        ovs(c)

    if "frr" in rspec:
        frr(c)

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
            append_cmds_ip_addr_add(c, dcmds, ip, "l3admin")

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

    for vm in rspec.get("vms", []):
        c = context.ContainerContext(c.gctx, vm)
        _make(c)


def ovs(c):
    rspec = c.rspec
    ovs = rspec["ovs"]
    cmds = [
        "systemctl start openvswitch",
    ]

    for bridge in ovs["bridges"]:
        br_name = bridge["name"]
        br_flows = []
        cmds += [
            f"ovs-vsctl --may-exist add-br {br_name}",
            f"ovs-vsctl set bridge {br_name} datapath_type=netdev protocols=OpenFlow10,OpenFlow11,OpenFlow12,OpenFlow13,OpenFlow14,OpenFlow15",
            f"ip link set up {br_name}",
        ]
        if bridge["kind"] == "external-ha":
            for link in rspec["_links"]:
                for vlan_id, vlan in link["vlan_map"].items():
                    peer_ovs = vlan.get("peer_ovs")
                    if peer_ovs is not None and peer_ovs["peer"] == br_name:
                        cmds += [f"ovs-vsctl --may-exist add-port {br_name} {link['peer_name']}.{vlan_id}"]
                        dryrun = c.exist_netdev(peer_ovs["peer_name"])
                        link_name = f"{br_name}-{peer_ovs['peer_name']}"
                        cmds += [
                            (f"ip link add {link_name} type veth peer name {peer_ovs['peer_name']}", dryrun),
                            (f"ip link set dev {link_name} mtu {link['mtu']}", dryrun),
                            (f"ip link set {link_name} up", dryrun),
                            (f"ethtool -K {link_name} tso off tx off", dryrun),
                            (f"ip link set dev {peer_ovs['peer_name']} up", dryrun),
                            (f"ethtool -K {peer_ovs['peer_name']} tso off tx off", dryrun),
                        ]
                        cmds += [f"ovs-vsctl --no-wait --may-exist add-port {br_name} {link_name}"]

            group1_ports = []
            for link in rspec["_links"]:
                for vlan_id, vlan in link["vlan_map"].items():
                    peer_ovs = vlan.get("peer_ovs")
                    if peer_ovs is not None and peer_ovs["peer"] == br_name:
                        ex_peer_name = f"{link['peer_name']}.{vlan_id}"
                        bgp_link_name = f"{br_name}-{peer_ovs['peer_name']}"
                        br_flows += [
                            # linklocalのbgp用の通信のingress
                            f"priority=800,ipv6,in_port={ex_peer_name},ipv6_src=fe80::/10,ipv6_dst=fe80::/10 actions=output:{bgp_link_name}",
                            f"priority=800,ipv6,in_port={ex_peer_name},ipv6_dst=ff02::/16 actions=output:{bgp_link_name}",
                            # linklocalのbgp用の通信のegress
                            f"priority=800,ipv6,in_port={bgp_link_name},ipv6_src=fe80::/10,ipv6_dst=fe80::/10 actions=output:{ex_peer_name}",
                            f"priority=800,ipv6,in_port={bgp_link_name},ipv6_dst=ff02::/16 actions=output:{ex_peer_name}",
                        ]
                        group1_ports += [f"bucket=watch_port:{ex_peer_name},actions=mod_dl_dst:{link['link_mac']},output:{ex_peer_name}"]
                buckets = ",".join(group1_ports)
                # egressの通信を冗長化させる
                cmds += [
                    f'ovs-ofctl -O OpenFlow15 mod-group --may-create {br_name} "group_id=1,type=select,selection_method=hash,fields(ip_src,ip_dst),'
                    + buckets
                    + '"'
                ]

        elif bridge["kind"] == "internal-vm":
            for link in rspec["vm_links"]:
                cmds += [f"ovs-vsctl --no-wait --may-exist add-port {br_name} {link['link_name']}"]

        for link in bridge.get("links", []):
            cmds += [
                f"ovs-vsctl --may-exist add-port {br_name} {link['link_name']}"
                + f" -- set interface {link['link_name']} type=patch options:peer={link['peer_name']}"
            ]
        for link in bridge.get("_links", []):
            cmds += [
                f"ovs-vsctl --may-exist add-port {br_name} {link['peer_name']}"
                + f" -- set interface {link['peer_name']} type=patch options:peer={link['link_name']}"
            ]

        if len(br_flows) > 0:
            br_flows += [
                "priority=0,actions=drop",
            ]
            flows_filepath = os.path.join(rspec["_script_dir"], f"{br_name}.flows")
            with open(flows_filepath, "w") as f:
                f.write("\n".join(br_flows))
            cmds += [f"ovs-ofctl -O OpenFlow15 replace-flows {br_name} {flows_filepath}"]

    c.exec(cmds, title="ovs")


def frr(c):
    rspec = c.rspec
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
    c.exec(cmds, title="frr_daemons")

    vtysh_cmds = [
        "configure terminal",
        "log file /var/log/frr/frr.log",
        "debug bgp keepalives",
        "debug bgp neighbor-events",
        "debug bgp updates",
        "ip forwarding",
        "ipv6 forwarding",
        "!",
    ]

    # prefix_listとroute_mapの定義
    for route_map in frr.get("route_maps", []):
        name = route_map["name"]
        for prefix in route_map.get("prefix_list", []):
            vtysh_cmds += [f"ip prefix-list {name} {prefix}"]
        vtysh_cmds += [f"route-map {name} {route_map['policy']} {route_map['order']}"]
        if len(route_map.get("prefix_list", [])) > 0:
            if route_map["version"] == 4:
                vtysh_cmds += [f"match ip address prefix-list {name}"]
            elif route_map["version"] == 0:
                vtysh_cmds += [f"match ipv6 address prefix-list {name}"]
        vtysh_cmds += ["exit"]

    # setup interfaces
    for link in rspec.get("links", []):
        if "bgp_peer_group" in link:
            vtysh_cmds += [
                f"interface {link['link_name']}",
                "ipv6 nd ra-interval 10",
                "no ipv6 nd suppress-ra",
                "!",
            ]
        for vlan_id, vlan in link.get("vlan_map", {}).items():
            if "bgp_peer_group" in vlan:
                vtysh_cmds += [
                    f"interface {link['link_name']}.{vlan_id}",
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
        for vlan_id, vlan in link.get("vlan_map", {}).items():
            if "bgp_peer_group" in vlan:
                if "peer_ovs" in vlan:
                    vtysh_cmds += [
                        f"interface {vlan['peer_ovs']['peer_name']}",
                        "ipv6 nd ra-interval 10",
                        "no ipv6 nd suppress-ra",
                        "!",
                    ]
                else:
                    vtysh_cmds += [
                        f"interface {link['peer_name']}.{vlan_id}",
                        "ipv6 nd ra-interval 10",
                        "no ipv6 nd suppress-ra",
                        "!",
                    ]

    # seup bgp
    vtysh_cmds += [
        f"router bgp {frr['asn']}",
        f"bgp router-id {frr['id']}",
        "bgp bestpath as-path multipath-relax",
        "no bgp ebgp-requires-policy",
        "no bgp network import-check",  # RIBにnetworkが存在するかをチェックするのを止める
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
        for vlan_id, vlan in link.get("vlan_map", {}).items():
            if "bgp_peer_group" in vlan:
                vtysh_cmds += [f"neighbor {link['link_name']}.{vlan_id} interface peer-group {vlan['bgp_peer_group']}"]
    for link in rspec.get("_links", []):
        if "bgp_peer_group" in link:
            vtysh_cmds += [f"neighbor {link['peer_name']} interface peer-group {link['bgp_peer_group']}"]
        for vlan_id, vlan in link.get("vlan_map", {}).items():
            if "bgp_peer_group" in vlan:
                if "peer_ovs" in vlan:
                    vtysh_cmds += [f"neighbor {vlan['peer_ovs']['peer_name']} interface peer-group {vlan['bgp_peer_group']}"]
                else:
                    vtysh_cmds += [f"neighbor {link['peer_name']}.{vlan_id} interface peer-group {vlan['bgp_peer_group']}"]

    vtysh_cmds += ["address-family ipv4 unicast"]
    for network in frr.get("ipv4_networks", []):
        vtysh_cmds += [f"network {network}"]
    for bgp_peer_group in frr.get("bgp_peer_groups", []):
        if "route_map_v4_in" in bgp_peer_group:
            vtysh_cmds += [f"neighbor {bgp_peer_group['name']} route-map {bgp_peer_group['route_map_v4_in']} in"]
        if "route_map_v4_out" in bgp_peer_group:
            vtysh_cmds += [f"neighbor {bgp_peer_group['name']} route-map {bgp_peer_group['route_map_v4_out']} out"]
    vtysh_cmds += ["exit-address-family"]

    vtysh_cmds += ["address-family ipv6 unicast"]
    for network in frr.get("ipv6_networks", []):
        vtysh_cmds += [f"network {network}"]
    for bgp_peer_group in frr.get("bgp_peer_groups", []):
        if "route_map_v6_in" in bgp_peer_group:
            vtysh_cmds += [f"neighbor {bgp_peer_group['name']} route-map {bgp_peer_group['route_map_v6_in']} in"]
        if "route_map_v6_out" in bgp_peer_group:
            vtysh_cmds += [f"neighbor {bgp_peer_group['name']} route-map {bgp_peer_group['route_map_v6_out']} out"]
    vtysh_cmds += ["exit-address-family"]

    vtysh_cmds += [
        "!",
        "line vty",
        "!",
    ]
    vtysh_cmds_str = "\n".join(vtysh_cmds)
    cmds = [f'vtysh -c "{vtysh_cmds_str}"']
    c.exec(cmds, title="frr_vtysh")
