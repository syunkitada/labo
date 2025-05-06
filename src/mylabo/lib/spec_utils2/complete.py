import copy
import ipaddress
import os

from mylabo.lib.spec_utils import ipam

MAC_OUI = [0x00, 0x16, 0x3E]


def update_dict(d, u):
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = update_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def complete_spec(spec):
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
        if splited_src[0] not in rspec:
            print(f"{splited_src[0]} is not found", rspec.keys())
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
        if spec["_node_map"][link["peer"]]["kind"] == "vm":
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
