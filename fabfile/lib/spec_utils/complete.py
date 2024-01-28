import copy
import ipaddress
import os

from lib.spec_utils import ipam

MAC_OUI = [0x00, 0x16, 0x3E]


def update_dict(d, u):
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = update_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def complete_spec(spec):
    spec["_script_dir"] = os.path.join(spec["common"]["nfs_path"], "labo_nodes", spec["common"]["namespace"])
    template_map = spec.get("template_map", {})
    node_map = spec.get("node_map", {})

    for _, network in spec.get("ipam", {}).items():
        if network["kind"] == "l2":
            network.update({"_next_ip": 2})
        elif network["kind"] == "l3":
            network.update({"_next_ip": 1})

    env_map = {}

    spec["_env_map"] = env_map

    vpcgw_map = spec.get("vpcgw_map", {})
    for rspec in vpcgw_map.values():
        rspec["_vpc_links_map"] = {}
        _complete_ip(rspec["vtep"], spec, rspec)

    _node_map = {}
    spec["_node_map"] = _node_map
    peer_links_map = {}

    def apply_template(rspec):
        if "templates" not in rspec:
            return
        tmp_spec = {}
        for template in rspec.get("templates", []):
            if template not in template_map:
                print(f"template is not found: name={template}, templates={template_map.keys()}")
                exit(1)
            template_spec = copy.deepcopy(template_map[template])
            update_dict(tmp_spec, template_spec)
        update_dict(tmp_spec, rspec)
        rspec.update(tmp_spec)

    def _init_node(rspec):
        peer_links_map[rspec["name"]] = []
        _node_map[rspec["name"]] = rspec
        apply_template(rspec)
        update_dict(rspec, node_map.get(rspec["name"], {}))
        for link in rspec.get("links", []):
            apply_template(link)
        if "frr" in rspec:
            apply_template(rspec["frr"])

        for child in rspec.get("childs", []):
            _init_node(child)

    for rspec in spec.get("nodes", []):
        _init_node(rspec)


    def _complete_node(i, rspec):
        _complete_links(i, spec, rspec, rspec.get("links", []))

        for link in rspec.get("links", []):
            peer_links_map[link["peer"]].append(link)
        rspec["_links"] = peer_links_map.get(rspec["name"], [])
        for link in rspec["_links"]:
            if "mtu" in rspec:
                if rspec["mtu"] < link["mtu"]:
                    link["mtu"] = rspec["mtu"]
            if "vpc_id" in rspec:
                link["vpc_id"] = rspec["vpc_id"]

        if "l3admin" in rspec:
            _complete_ips(rspec["l3admin"].get("ips", []), spec, rspec)

        if rspec["kind"] == "vm":
            rspec["_hostname"] = rspec["name"].replace('_', '-') + "." + spec["conf"]["domain"]

        elif rspec["kind"] == "container":
            rspec["_hostname"] = f"{spec['common']['namespace']}-{rspec['name']}"
            _complete_ips(rspec.get("lo_ips", []), spec, rspec)
            for bridge in rspec.get("bridges", []):
                if "mtu" not in bridge:
                    bridge["mtu"] = rspec.get("mtu", 1500)
                _complete_ips(bridge.get("ips", []), spec, rspec)

            for ip_rule in rspec.get("ip_rules", []):
                ip_rule["rule"] = _complete_value(ip_rule["rule"], spec, rspec)

            ovs = rspec.get("ovs")
            if ovs is not None:
                _complete_ips(ovs.get("admin_ips", []), spec, rspec)
                ovs_peer_links_map = {}
                for bridge in ovs.get("bridges", []):
                    ovs_peer_links_map[bridge["name"]] = []
                for bridge in ovs.get("bridges", []):
                    br_name = bridge["name"]
                    for link in bridge.get("links", []):
                        if link.get("kind", "") == "local":
                            link["link_name"] = "local"
                            continue
                        link["link_name"] = f"{br_name}_{link['peer']}"
                        link["peer_name"] = f"{link['peer']}_{br_name}"
                        # ovsのinterface nameは15字までなので、br-というprefixは削ります
                        # https://man7.org/linux/man-pages/man5/ovs-vswitchd.conf.db.5.html
                        link["link_name"] = link["link_name"].replace("br-", "")
                        link["peer_name"] = link["peer_name"].replace("br-", "")
                        # それでも15字を超える場合は、そのまま削る
                        if len(link["link_name"]) > 15:
                            link["link_name"] = link["link_name"][:15]
                        if len(link["peer_name"]) > 15:
                            link["peer_name"] = link["peer_name"][:15]
                        ovs_peer_links_map[link["peer"]].append(link)
                    bridge["_links"] = ovs_peer_links_map.get(br_name, [])

            _complete_links(i, spec, rspec, rspec.get("child_links", []))
            for child in rspec.get("childs", []):
                peer_links_map[child["name"]] = []
            for link in rspec.get("child_links", []):
                peer_links_map[link["peer"]].append(link)
            for childi, child in enumerate(rspec.get("childs", [])):
                child["parent"] = rspec
                _complete_node(childi, child)

            frr = rspec.get("frr")
            if frr is not None:
                frr["id"] = _complete_value(frr["id"], spec, rspec)
                frr["asn"] = _complete_value(frr["asn"], spec, rspec)
                for i, value in enumerate(frr.get("ipv4_networks", [])):
                    frr["ipv4_networks"][i] = _complete_value(value, spec, rspec)
                for i, value in enumerate(frr.get("ipv6_networks", [])):
                    frr["ipv6_networks"][i] = _complete_value(value, spec, rspec)
                for route_map in frr.get("route_map", {}).values():
                    for i, value in enumerate(route_map.get("prefix_list", [])):
                        route_map["prefix_list"][i] = _complete_value(value, spec, rspec)

            if "sid" in rspec:
                rspec["sid"]["inet"] = _complete_value(rspec["sid"]["inet"], spec, rspec)
                _complete_ip(rspec["sid"], spec, rspec)

            if "vpcgw" in rspec:
                rspec["_vpcgw"] = vpcgw_map[rspec["vpcgw"]]


        for route in rspec.get("routes", []):
            route["dst"] = _complete_value(route["dst"], spec, rspec)
            route["via"] = _complete_value(route["via"], spec, rspec)
        for route in rspec.get("routes6", []):
            route["dst"] = _complete_value(route["dst"], spec, rspec)
            route["via"] = _complete_value(route["via"], spec, rspec)

        rspec["_script_index"] = 0
        rspec["_script_dir"] = os.path.join(spec["common"]["nfs_path"], "labo_nodes", rspec["_hostname"])

        for key, value in rspec.get("var_map", {}).items():
            rspec["var_map"][key] = _complete_value(value, spec, rspec)

    def _complete_node_at_last(_, rspec):
        for j, cmd in enumerate(rspec.get("cmds", [])):
            rspec["cmds"][j] = _complete_value(cmd, spec, rspec)

        for j, test in enumerate(rspec.get("tests", [])):
            if test["kind"] == "ping":
                for target in test["targets"]:
                    target["dst"] = _complete_value(target["dst"], spec, rspec)

        for childi, child in enumerate(rspec.get("childs", [])):
            _complete_node_at_last(childi, child)

        if "ansible" in rspec:
            if 'frr' in rspec['ansible']['roles']:
                frr_interfaces = []
                for link in rspec.get("links", []):
                    if "bgp_peer_group" in link:
                        frr_interfaces += [{
                            "name": link['link_name'],
                            "bgp_peer_group": link['bgp_peer_group'],
                        }]
                    for vlan_id, vlan in link.get("vlan_map", {}).items():
                        if "bgp_peer_group" in vlan:
                            frr_interfaces += [{
                                "name": f"{link['link_name']}.{vlan_id}",
                                "bgp_peer_group": vlan['bgp_peer_group'],
                            }]
                for link in rspec.get("_links", []):
                    if "bgp_peer_group" in link:
                        frr_interfaces += [{
                            "name": link['peer_name'],
                            "bgp_peer_group": link['bgp_peer_group'],
                        }]
                    for vlan_id, vlan in link.get("vlan_map", {}).items():
                        if "bgp_peer_group" in vlan:
                            if "peer_ovs" in vlan:
                                frr_interfaces += [{
                                    "name": vlan['peer_ovs']['peer_name'],
                                    "bgp_peer_group": vlan['bgp_peer_group'],
                                }]
                            else:
                                frr_interfaces += [{
                                    "name": f"{link['peer_name']}.{vlan_id}",
                                    "bgp_peer_group": vlan['bgp_peer_group'],
                                }]

                rspec['ansible']['vars']['frr_interfaces'] = frr_interfaces

            if "vars" in rspec['ansible']:
                def _complete_dict(data):
                    if isinstance(data, list):
                        for i, value in enumerate(data):
                            if isinstance(value, str):
                                data[i] = _complete_value(value, spec, rspec)
                            if isinstance(value, dict):
                                _complete_dict(value)
                            if isinstance(value, list):
                                _complete_dict(value)
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, str):
                                data[key] = _complete_value(value, spec, rspec)
                            if isinstance(value, dict):
                                _complete_dict(value)
                            if isinstance(value, list):
                                _complete_dict(value)

                _complete_dict(rspec['ansible']['vars'])

        if "ovs" in rspec:
            ovs = rspec["ovs"]
            for bridge in ovs.get("bridges", []):
                br_kind = bridge.get("kind", "")
                if br_kind == "vxlan-vpc-vm":
                    own_vm_map = {}
                    for vm in rspec.get("vms", []):
                        own_vm_map[vm["name"]] = vm

                    br_vpc_id = bridge["vpc_id"]
                    ex_vteps = []
                    for node in _node_map.values():
                        if "vpc_id" in node and node["name"] not in own_vm_map and node["vpc_id"] == br_vpc_id:
                            tun_dst = node["parent"]["_links"][0]["peer_ips"][0]["ip"]
                            if "admin_ips" in node["parent"]["ovs"]:
                                tun_dst = node["parent"]["ovs"]["admin_ips"][0]["ip"]
                            ex_vteps.append(
                                {
                                    "dst": node,
                                    "tun_dst": tun_dst,
                                }
                            )
                    bridge["ex_vteps"] = ex_vteps

                    tun_dst = rspec["_links"][0]["peer_ips"][0]["ip"]
                    if "admin_ips" in rspec["ovs"]:
                        tun_dst = rspec["ovs"]["admin_ips"][0]["ip"]
                    # if "vpcgw" not in bridge:
                    #     bridge["vpcgw"] = rspec["vpcgw"]
                    # vpcgw = vpcgw_map[bridge["vpcgw"]]
                    # bridge["_vpcgw"] = vpcgw
                    # vpc_links_map = vpcgw["_vpc_links_map"]
                    # for child_link in rspec.get("child_links", []):
                    #     if child_link["vpc_id"] != bridge["vpc_id"]:
                    #         continue
                    #     if child_link["vpc_id"] not in vpc_links_map:
                    #         vpc_links_map[child_link["vpc_id"]] = []
                    #     for ip in child_link["peer_ips"]:
                    #         vpc_links_map[child_link["vpc_id"]].append(
                    #             {
                    #                 "ip": ip["ip"],
                    #                 "eip": ip["eip"],
                    #                 "tun_dst": tun_dst,
                    #             }
                    #         )

    for i, rspec in enumerate(spec.get("nodes", [])):
        _complete_node(i, rspec)

    for i, rspec in enumerate(spec.get("nodes", [])):
        _complete_node_at_last(i, rspec)

    vip_map = spec.get("vip_map", {})
    for rspec in vip_map.values():
        _complete_ip(rspec["vip"], spec, rspec)
        _complete_ip(rspec["tunvip"], spec, rspec)
        if "evip" in rspec:
            _complete_ip(rspec["evip"], spec, rspec)
        for member in rspec.get("members", []):
            member["_node"] = _node_map[member["name"]]

    return


def _complete_value(value, spec, node, is_get_src=False):
    if not isinstance(value, str):
        return value

    try:
        compi = value.find("<%=")
        compri = value.find("%>", compi)
        if compi >= 0 and compri > 1:
            value_prefix = value[0:compi]
            value_suffix = value[compri + 2 :]  # noqa
            value = value[compi + 3 : compri]  # noqa
            value = value.strip()
            funci = value.find("(")
            funcri = value.rfind(")")
            func = value[:funci]
            arg = value[funci + 1 : funcri]  # noqa
            if funci == -1 or funcri == -1:
                value = _get_src(value, spec, node)
            elif func == "assign_inet4":
                value = ipam.assign_inet4(arg, spec)
            elif func == "assign_ip4":
                value = ipam.inet_to_ip(ipam.assign_inet4(arg, spec))
            elif func == "gateway_inet4":
                value = ipam.gateway_inet4(arg, spec)
            elif func == "inet_to_ip":
                value = ipam.inet_to_ip(_complete_value(arg, spec, node, True))
            elif func == "gateway_ip":
                value = ipam.gateway_ip(_complete_value(arg, spec, node, True))
            elif func == "inet4_to_inet6":
                value = ipam.inet4_to_inet6(_complete_value(arg, spec, node, True))
            elif func == "ipv4_to_asn":
                value = ipam.ipv4_to_asn(_complete_value(arg, spec, node, True))
            elif func == "asn_to_sid":
                value = ipam.asn_to_sid(_complete_value(arg, spec, node, True))
            else:
                raise Exception(f"unexpected func: {func}")
            return _complete_value(value_prefix + str(value) + value_suffix, spec, node)
        else:
            if is_get_src:
                return _get_src(value, spec, node)
            else:
                return value
    except Exception as e:
        print(f"value={value}")
        raise (e)


def _get_src(src, spec={}, rspec={}):
    splited_src = src.split(".")
    if splited_src[0] in ["_node_map", "vpcgw_map", "ipam", "vip_map"]:
        rspec = spec

    tmp_src = None
    if isinstance(rspec, dict):
        tmp_src = rspec[splited_src[0]]
    elif isinstance(rspec, list):
        tmp_src = rspec[int(splited_src[0])]

    if tmp_src is not None and isinstance(tmp_src, dict) or isinstance(tmp_src, list):
        return _get_src(".".join(splited_src[1:]), spec, tmp_src)
    else:
        return tmp_src


def _complete_links(i, spec, rspec, links):
    for j, link in enumerate(links):
        _complete_ips(link.get("ips", []), spec, rspec)
        _complete_ips(link.get("peer_ips", []), spec, rspec)
        if "mtu" not in link:
            link["mtu"] = rspec.get("mtu", 1500)
        if spec['_node_map'][link['peer']]['kind'] == 'vm':
            link["kind"] = "tap"
        else:
            link["kind"] = "veth"
        link["src_name"] = rspec["name"]
        link["link_name"] = f"{rspec['name']}_{j}_{link['peer']}"
        link["peer_name"] = f"{link['peer']}_{j}_{rspec['name']}"
        if "link_mac" not in link:
            link["link_mac"] = ":".join(map(lambda x: "%02x" % x, MAC_OUI + [i, j, 0]))
        if "peer_mac" not in link:
            link["peer_mac"] = ":".join(map(lambda x: "%02x" % x, MAC_OUI + [i, j, 1]))


def _complete_ips(ips, spec, rspec):
    for ip in ips:
        _complete_ip(ip, spec, rspec)


def _complete_ip(ip, spec, rspec):
    ip["inet"] = _complete_value(ip["inet"], spec, rspec)
    ip_interface = ipaddress.ip_interface(ip["inet"])
    ip["inet_compressed"] = ip_interface.compressed
    ip["inet_exploded"] = ip_interface.exploded
    ip["ip"] = str(ip_interface.ip)
    ip["version"] = ip_interface.version
    ip["network"] = str(ip_interface.network)
    ip_network = ipaddress.ip_network(ip["network"])
    if ip_network.version == 4 and ip_network.prefixlen < 32:
        ip["gateway_ip"] = str(ip_network[1])
    if "eip" in ip:
        ip["eip"] = _complete_value(ip["eip"], spec, rspec)
