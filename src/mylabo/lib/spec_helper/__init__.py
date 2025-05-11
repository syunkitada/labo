from . import ipam

func_map = {
    "gateway_inet4": ipam.gateway_inet4,
    "assign_inet4": ipam.assign_inet4,
}


def handle(func: str, data, arg):
    if func in func_map:
        return func_map[func](data, arg)
    else:
        raise Exception(f"Unexpected func: {func}")
