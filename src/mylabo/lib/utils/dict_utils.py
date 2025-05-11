from mylabo.lib import spec_helper


def update_dict(d: dict, u: dict):
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = update_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def complete_data(root_data: dict, data: dict | list):
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) or isinstance(v, list):
                data[k] = complete_data(root_data, v)
            elif isinstance(v, str):
                data[k] = complete_value(root_data, v)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            if isinstance(v, dict) or isinstance(v, list):
                data[i] = complete_data(root_data, v)
            elif isinstance(v, str):
                data[i] = complete_value(root_data, v)

    return data


def complete_value(root_data: dict, value: str):
    try:
        compi = value.find("<%=")
        compri = value.find("%>", compi)
        if compi >= 0 and compri > 1:
            value_prefix = value[0:compi]
            value_suffix = value[compri + 2 :]  # noqa
            _value = value[compi + 3 : compri]  # noqa
            _value = _value.strip()
            funci = _value.find("(")
            funcri = _value.rfind(")")
            func = _value[:funci]
            arg = _value[funci + 1 : funcri]  # noqa
            if funci == -1 or funcri == -1:
                _value = reference_value(root_data, _value)
            else:
                spec_helper.handle(func, root_data, arg)
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

            return complete_value(root_data, value_prefix + str(_value) + value_suffix)

        else:
            return value

    except Exception as e:
        print(f"value={value}")
        raise (e)


def reference_value(data: dict | list, reference_key: str):
    splited_src = reference_key.split(".")

    tmp_data = None
    if isinstance(data, dict):
        if splited_src[0] not in data:
            print(f"{splited_src[0]} is not found", data.keys())
        tmp_data = data[splited_src[0]]
    elif isinstance(data, list):
        tmp_data = data[int(splited_src[0])]

    if tmp_data is not None and isinstance(tmp_data, dict) or isinstance(tmp_data, list):
        return reference_value(tmp_data, ".".join(splited_src[1:]))
    else:
        return tmp_data
