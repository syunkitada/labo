import os
import copy
import ipaddress

from mylabo.lib import spec_helper


def init_spec(spec: dict, file: str):
    spec_dir = os.path.dirname(os.path.realpath(file))
    namespace = file.rsplit("/", 1)[1].split(".", 1)[0].replace("_", "-")
    if "namespace" not in spec:
        spec["namespace"] = namespace
    spec["_script_dir"] = os.path.join(spec["local_namespaces_dir"], spec["kind"].lower(), spec["namespace"])
    spec["_spec_dir"] = spec_dir


def update_dict(d: dict, u: dict):
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = update_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def apply_template(root_data: dict, data: dict):
    if "templates" not in data:
        return data
    if "template_map" not in root_data:
        raise Exception("template_map is not found in root_data")

    template_map = root_data["template_map"]

    tmp_data = {}
    for template in data["templates"]:
        if template not in template_map:
            raise Exception(f"template {template} is not found in template_map")
        template = copy.deepcopy(template_map[template])
        update_dict(tmp_data, template)

    update_dict(tmp_data, data)
    data.update(tmp_data)


def complete_template(spec: dict):
    return _complete_template(spec, spec)


def _complete_template(root_data: dict, data: dict | list):
    if isinstance(data, dict):
        apply_template(root_data, data)

        for k, v in data.items():
            if isinstance(v, dict) or isinstance(v, list):
                data[k] = _complete_template(root_data, v)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            if isinstance(v, dict) or isinstance(v, list):
                data[i] = _complete_template(root_data, v)

    return data


def must_complete_data(spec: dict):
    return _complete_data(spec, "", spec, must_complete=True)


def complete_data(spec: dict):
    return _complete_data(spec, "", spec)


def _complete_data(root_data: dict, key: str, data: dict | list, must_complete: bool = False):
    if key == "template_map":
        return

    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) or isinstance(v, list):
                data[k] = _complete_data(root_data, k, v, must_complete)
            elif isinstance(v, str):
                data[k] = complete_value(root_data, v, must_complete)
        if "inet" in data:
            complete_inet_data(data)
    elif isinstance(data, list):
        is_node = False
        if key == "nodes":
            is_node = True
        for i, v in enumerate(data):
            if isinstance(v, dict) or isinstance(v, list):
                if is_node:
                    print(f"Complete node: {v['name']}")
                    root_data["_referer"]["_node"] = v
                data[i] = _complete_data(root_data, str(i), v, must_complete)
            elif isinstance(v, str):
                data[i] = complete_value(root_data, v, must_complete)

    return data


def complete_inet_data(inet_data: dict):
    ip_interface = ipaddress.ip_interface(inet_data["inet"])
    inet_data["inet_compressed"] = ip_interface.compressed
    inet_data["inet_exploded"] = ip_interface.exploded
    inet_data["ip"] = str(ip_interface.ip)
    inet_data["version"] = ip_interface.version
    inet_data["network"] = str(ip_interface.network)
    ip_network = ipaddress.ip_network(inet_data["network"])
    if ip_network.version == 4 and ip_network.prefixlen < 32:
        inet_data["gateway_ip"] = str(ip_network[1])


def complete_value(root_data: dict, value: str, must_complete: bool = False) -> str:
    try:
        compi = value.find("<%=")
        compri = value.find("%>", compi)
        if compi >= 0 and compri > 1:
            value_prefix = value[0:compi]
            value_suffix = value[compri + 2 :]  # noqa
            _value = value[compi + 3 : compri]  # noqa
            _value = _value.strip()

            def _complete(txt: str) -> str | None:
                if txt.startswith('"') and txt.endswith('"'):
                    return txt[1:-1]
                if txt.startswith("'") and txt.endswith("'"):
                    return txt[1:-1]

                funci = txt.find("(")
                funcri = txt.rfind(")")
                func = txt[:funci]
                arg = txt[funci + 1 : funcri]  # noqa

                if funci != -1 and funcri != -1:
                    txt = _complete(arg)
                    if txt is None:
                        return None
                    txt = spec_helper.handle(func, root_data, _complete(arg))
                    return txt

                return reference_value(root_data, root_data, txt)

            _value = _complete(_value)
            if _value is None:
                return value

            # TODO
            # elif func == "assign_inet4":
            #     value = ipam.assign_inet4(arg, spec)
            # elif func == "assign_ip4":
            #     value = ipam.inet_to_ip(ipam.assign_inet4(arg, spec))
            # elif func == "gateway_inet4":
            #     value = ipam.gateway_inet4(arg, spec)
            # elif func == "inet_to_ip":
            #     value = ipam.inet_to_ip(_complete_value(arg, spec, node, True))
            # elif func == "gateway_ip":
            #     value = ipam.gateway_ip(_complete_value(arg, spec, node, True))
            # elif func == "inet4_to_inet6":
            #     value = ipam.inet4_to_inet6(_complete_value(arg, spec, node, True))
            # elif func == "ipv4_to_asn":
            #     value = ipam.ipv4_to_asn(_complete_value(arg, spec, node, True))
            # elif func == "asn_to_sid":
            #     value = ipam.asn_to_sid(_complete_value(arg, spec, node, True))
            # else:
            #     raise Exception(f"unexpected func: {func}")

            return complete_value(root_data, value_prefix + str(_value) + value_suffix, must_complete=must_complete)

        else:
            return value

    except Exception as e:
        print(f"value={value}, exception={e}")
        if must_complete:
            raise
        return value


def reference_value(root_data: dict, data: dict | list, reference_key: str) -> str | None:
    splited_src = reference_key.split(".")

    tmp_data = None
    if isinstance(data, dict):
        if splited_src[0] in data:
            tmp_data = data[splited_src[0]]
        elif splited_src[0] in root_data["_referer"]:
            tmp_data = root_data["_referer"][splited_src[0]]
        else:
            print(f"{splited_src[0]} is not found", data.keys())
    elif isinstance(data, list):
        tmp_data = data[int(splited_src[0])]

    if tmp_data is None:
        return None

    if isinstance(tmp_data, dict) or isinstance(tmp_data, list):
        return reference_value(root_data, tmp_data, ".".join(splited_src[1:]))

    return tmp_data


def modify_spec(spec: dict):
    for spec_modification in spec.get("spec_modifications", []):
        if "overwrite_node" in spec_modification:
            if "nodes" not in spec["spec"]:
                raise Exception("nodes is not found in spec")

            for node in spec["spec"]["nodes"]:
                if node["name"] in spec_modification["overwrite_node"]:
                    update_dict(node, spec_modification["overwrite_node"][node["name"]])

        elif "extend_nodes" in spec_modification:
            if "nodes" not in spec["spec"]:
                raise Exception("nodes is not found in spec")

            spec["spec"]["nodes"].extend(spec_modification["extend_nodes"])


def complete_nodes(spec: dict):
    if "nodes" not in spec["spec"]:
        return

    node_map = {}
    for node in spec["spec"]["nodes"]:
        if node["kind"] == "container":
            node["_hostname"] = f"{node['name']}.{spec['namespace']}"
        else:
            node["_hostname"] = f"{node['name'].replace('_', '-')}.{spec['namespace']}.{spec['spec']['domain']}"

        node["spec"]["_links"] = []

        node_map[node["name"]] = node
    spec["_referer"]["_node_map"] = node_map

    _complete_links(spec, node_map)


def _complete_links(spec: dict, node_map: dict):
    for node_index, node in enumerate(spec["spec"]["nodes"]):
        if "links" not in node["spec"]:
            continue

        for link_index, link in enumerate(node["spec"]["links"]):
            if "peer" not in link:
                raise Exception(f"peer is not found in link: {link}")

            peer_node = node_map.get(link["peer"])
            if peer_node is None:
                raise Exception(f"peer node {link['peer']} is not found in node_map")

            _complete_link(node_index, node, peer_node, link_index, link)
            peer_node["spec"]["_links"].append(link)


MAC_OUI = [0x00, 0x16, 0x3E]


def _complete_link(node_index: int, node: dict, peer_node, link_index: int, link: dict):
    if "mtu" not in link:
        link["mtu"] = 1500

    if "kind" not in link:
        if node["kind"] == "vm" or peer_node["kind"] == "vm":
            link["kind"] = "tap"
        elif node["kind"] == "container":
            link["kind"] = "veth"
        else:
            raise Exception(f"unexpected node kind: {node['kind']}")

    link["src_name"] = node["name"]
    link["link_name"] = f"{node['name']}_{link_index}_{link['peer']}"
    link["peer_name"] = f"{link['peer']}_{link_index}_{node['name']}"
    if "link_mac" not in link:
        link["link_mac"] = ":".join(map(lambda x: "%02x" % x, MAC_OUI + [node_index, link_index, 0]))
    if "peer_mac" not in link:
        link["peer_mac"] = ":".join(map(lambda x: "%02x" % x, MAC_OUI + [node_index, link_index, 1]))
