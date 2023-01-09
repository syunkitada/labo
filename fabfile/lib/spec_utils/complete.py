import copy
import os
import ipaddress

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

    infra_map = {}
    for rspec in spec.get("infras", []):
        if rspec["name"] == "mysql":
            env_map["MYSQL_ROOT_PASSWORD"] = rspec.get("root_password", "rootpass")
            env_map["MYSQL_ADMIN_USER"] = rspec.get("admin_user", "admin")
            env_map["MYSQL_ADMIN_PASSWORD"] = rspec.get("admin_password", "adminpass")
        elif rspec["name"] == "pdns":
            env_map["PDNS_LOCAL_ADDRESS"] = rspec.get("local_address", "127.0.0.1")
            env_map["PDNS_DOMAIN"] = spec["conf"]["domain"]
            for record in rspec.get("records", []):
                record["fqdn"] = record["name"] + "." + spec["conf"]["domain"]

        infra_map[rspec["name"]] = rspec
    spec["_infra_map"] = infra_map
    spec["_env_map"] = env_map

    vm_image_map = spec.get("vm_image_map", {})
    for name, rspec in vm_image_map.items():
        rspec["name"] = name
        rspec["_path"] = os.path.join(spec["conf"]["vm_images_dir"], name)

    vpcgw_map = spec.get("vpcgw_map", {})
    for rspec in vpcgw_map.values():
        _complete_ip(rspec["vtep"], spec, rspec)

    _node_map = {}
    spec["_node_map"] = _node_map
    peer_links_map = {}
    for rspec in spec.get("nodes", []):
        peer_links_map[rspec["name"]] = []

    def _complete_node(i, rspec):
        _node_map[rspec["name"]] = rspec
        tmp_spec = {}
        for template in rspec.get("templates", []):
            if template not in template_map:
                print(f"template is not found: name={template}, templates={template_map.keys()}")
                exit(1)
            template_spec = copy.deepcopy(template_map[template])
            update_dict(tmp_spec, template_spec)
        update_dict(tmp_spec, rspec)
        update_dict(tmp_spec, node_map.get(rspec["name"], {}))
        rspec.update(tmp_spec)

        _complete_links(i, spec, rspec, rspec.get("links", []))

        for link in rspec.get("links", []):
            peer_links_map[link["peer"]].append(link)
        rspec["_links"] = peer_links_map.get(rspec["name"], [])
        for link in rspec["_links"]:
            if "mtu" in rspec:
                if rspec["mtu"] < link["mtu"]:
                    link["mtu"] = rspec["mtu"]
            if "tenant" in rspec:
                link["tenant"] = rspec["tenant"]

        if "l3admin" in rspec:
            _complete_ips(rspec["l3admin"].get("ips", []), spec, rspec)

        if rspec["kind"] == "vm":
            vm_dir = os.path.join(spec["conf"]["vms_dir"], rspec["name"])
            rspec["_hostname"] = rspec["name"] + "." + spec["conf"]["domain"]
            rspec["_image"] = vm_image_map[rspec["image"]]
            rspec["_vm_dir"] = vm_dir
            rspec["_image_path"] = os.path.join(vm_dir, "img")
            rspec["_monitor_socket_path"] = os.path.join(vm_dir, "monitor.sock")
            rspec["_serial_socket_path"] = os.path.join(vm_dir, "serial.sock")
            rspec["_serial_log_path"] = os.path.join(vm_dir, "serial.log")
            rspec["_config_image_path"] = os.path.join(vm_dir, "config.img")
            rspec["_metadata_path"] = os.path.join(vm_dir, "meta-data")
            rspec["_userdata_path"] = os.path.join(vm_dir, "user-data")

        if rspec["kind"] == "container":
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
                        ovs_peer_links_map[link["peer"]].append(link)
                    bridge["_links"] = ovs_peer_links_map.get(br_name, [])

            _complete_links(i, spec, rspec, rspec.get("vm_links", []))
            for vm in rspec.get("vms", []):
                peer_links_map[vm["name"]] = []
            for link in rspec.get("vm_links", []):
                peer_links_map[link["peer"]].append(link)
            for vmi, vm in enumerate(rspec.get("vms", [])):
                vm["hv"] = rspec
                _complete_node(vmi, vm)

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

        # end if rspec["kind"] == "container":
        else:
            rspec["_hostname"] = f"{spec['common']['namespace']}-{rspec['name']}"

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

        for vmi, vm in enumerate(rspec.get("vms", [])):
            _complete_node_at_last(vmi, vm)

        if "ovs" in rspec:
            ovs = rspec["ovs"]
            for bridge in ovs.get("bridges", []):
                if bridge["kind"] == "vxlan-tenant-vm":
                    if "vpcgw" in bridge:
                        bridge["_vpcgw"] = vpcgw_map[bridge["vpcgw"]]

                    own_vm_map = {}
                    for vm in rspec.get("vms", []):
                        own_vm_map[vm["name"]] = vm

                    br_tenant = bridge["tenant"]
                    ex_vteps = []
                    for node in _node_map.values():
                        if "tenant" in node and node["name"] not in own_vm_map and node["tenant"] == br_tenant:
                            tun_dst = node["hv"]["_links"][0]["peer_ips"][0]["ip"]
                            if "admin_ips" in node["hv"]["ovs"]:
                                tun_dst = node["hv"]["ovs"]["admin_ips"][0]["ip"]
                            ex_vteps.append(
                                {
                                    "dst": node,
                                    "tun_dst": tun_dst,
                                }
                            )
                    bridge["ex_vteps"] = ex_vteps

    for i, rspec in enumerate(spec.get("nodes", [])):
        _complete_node(i, rspec)

    for i, rspec in enumerate(spec.get("nodes", [])):
        _complete_node_at_last(i, rspec)

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
    if splited_src[0] in ["_node_map", "vpcgw_map", "ipam"]:
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
    ip["ip"] = str(ip_interface.ip)
    ip["version"] = ip_interface.version
    ip["network"] = str(ip_interface.network)
    ip_network = ipaddress.ip_network(ip["network"])
    if ip_network.version == 4 and ip_network.prefixlen < 32:
        ip["gateway_ip"] = str(ip_network[1])
