# container_frr


def make(rc):
    rspec = rc.rspec

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
    rc.exec(cmds, title="frr_daemons")

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
    for name, route_map in frr.get("route_map", {}).items():
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
        "no bgp default ipv4-unicast",  # BGPピアを設定してもneighbor activateを実行するまでIPv4ユニキャスト経路情報の交換を開始しないようにする
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
    vtysh_cmds += ["neighbor ADMIN activate"]
    vtysh_cmds += ["exit-address-family"]

    vtysh_cmds += ["address-family ipv6 unicast"]
    for network in frr.get("ipv6_networks", []):
        vtysh_cmds += [f"network {network}"]
    if "sid" in rspec:
        vtysh_cmds += [f"network {rspec['sid']['network']}"]
    for bgp_peer_group in frr.get("bgp_peer_groups", []):
        if "route_map_v6_in" in bgp_peer_group:
            vtysh_cmds += [f"neighbor {bgp_peer_group['name']} route-map {bgp_peer_group['route_map_v6_in']} in"]
        if "route_map_v6_out" in bgp_peer_group:
            vtysh_cmds += [f"neighbor {bgp_peer_group['name']} route-map {bgp_peer_group['route_map_v6_out']} out"]
    vtysh_cmds += ["neighbor ADMIN activate"]
    vtysh_cmds += ["exit-address-family"]

    vtysh_cmds += [
        "!",
        "line vty",
        "!",
    ]
    vtysh_cmds_str = "\n".join(vtysh_cmds)
    cmds = [f'vtysh -c "{vtysh_cmds_str}"']
    rc.exec(cmds, title="frr_vtysh")
