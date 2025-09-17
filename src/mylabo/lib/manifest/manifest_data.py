import ipaddress

from mylabo.lib.manifest import functions

TEMPLATE_START_MARKER = "<%="
TEMPLATE_END_MARKER = "%>"
REFERER_KEY = "_referer"
NODE_KEY = "_node"
NODES_KEY = "nodes"
INET_KEY = "inet"
MAX_RECURSION_DEPTH = 10


def complete(manifest: dict, times: int):
    return _complete_recursively(manifest, "", manifest, times)


def _complete_recursively(root_manifest: dict, key: str, data: dict | list, times: int):
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) or isinstance(v, list):
                data[k] = _complete_recursively(root_manifest, k, v, times)
            elif isinstance(v, str):
                data[k] = complete_value(root_manifest, v, times)
        if INET_KEY in data:
            complete_inet_data(data)
    elif isinstance(data, list):
        is_node = False
        if key == NODES_KEY:
            is_node = True
        for i, v in enumerate(data):
            if isinstance(v, dict) or isinstance(v, list):
                if is_node:
                    print(f"Complete node: {v['name']}")
                    root_manifest[REFERER_KEY][NODE_KEY] = v
                data[i] = _complete_recursively(root_manifest, str(i), v, times)
            elif isinstance(v, str):
                data[i] = complete_value(root_manifest, v, times)

    return data


def complete_inet_data(inet_data: dict):
    inet = inet_data["inet"]

    _compi = inet.find(TEMPLATE_START_MARKER)
    _compri = inet.find(TEMPLATE_END_MARKER, _compi)
    if _compi >= 0 and _compri > 1:
        print(f"Skip incomplete inet data: {inet}")
        return

    ip_interface = ipaddress.ip_interface(inet)
    inet_data["inet_compressed"] = ip_interface.compressed
    inet_data["inet_exploded"] = ip_interface.exploded
    inet_data["ip"] = str(ip_interface.ip)
    inet_data["version"] = ip_interface.version
    inet_data["network"] = str(ip_interface.network)
    ip_network = ipaddress.ip_network(inet_data["network"])
    if ip_network.version == 4 and ip_network.prefixlen < 32:
        inet_data["gateway_ip"] = str(ip_network[1])


def complete_value(root_manifest: dict, value: str, times: int = 0) -> str:
    try:
        compi = value.find(TEMPLATE_START_MARKER)
        compri = value.find(TEMPLATE_END_MARKER, compi)
        if compi >= 0 and compri > 1:
            value_prefix = value[0:compi]
            value_suffix = value[compri + len(TEMPLATE_END_MARKER) :]  # noqa
            _value = value[compi + len(TEMPLATE_START_MARKER) : compri]  # noqa
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
                    txt = functions.handle(func, root_manifest, _complete(arg))
                    return txt

                tmp_value = reference_value(root_manifest, root_manifest, txt)
                if not isinstance(tmp_value, str):
                    return tmp_value
                else:
                    _compi = tmp_value.find(TEMPLATE_START_MARKER)
                    _compri = tmp_value.find(TEMPLATE_END_MARKER, _compi)
                    if _compi >= 0 and _compri > 1:
                        return None
                    else:
                        return tmp_value

            _value = _complete(_value)
            if _value is None:
                return value

            return complete_value(
                root_manifest, value_prefix + str(_value) + value_suffix, times
            )

        else:
            return value

    except Exception as e:
        print(f"times={times}, value={value}, exception={e}")
        if times < 0:
            raise
        return value


def reference_value(
    root_manifest: dict, data: dict | list, reference_key: str
) -> str | None:
    splited_src = reference_key.split(".")

    tmp_data = None
    if isinstance(data, dict):
        if splited_src[0] in data:
            tmp_data = data[splited_src[0]]
        elif splited_src[0] in root_manifest[REFERER_KEY]:
            tmp_data = root_manifest[REFERER_KEY][splited_src[0]]
        else:
            print(f"{splited_src[0]} is not found", data.keys())
    elif isinstance(data, list):
        tmp_data = data[int(splited_src[0])]

    if tmp_data is None:
        return None

    if isinstance(tmp_data, dict) or isinstance(tmp_data, list):
        return reference_value(root_manifest, tmp_data, ".".join(splited_src[1:]))

    return tmp_data
