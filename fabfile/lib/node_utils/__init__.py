import traceback
from fabric import Connection

from lib import colors
from . import container_context, router, container, vm, vm_image


def make(t):
    print(f"{t.cmd} node {t.rspec['name']}: start {t.next}")
    result = None
    try:
        if t.rspec["kind"] == "gw":
            result = router.cmd(t.cmd, t.c, t.spec, t.rspec)
        elif t.rspec["kind"] == "container":
            if t.rc is None:
                t.rc = container_context.Context(t)
            result = container.cmd(t)
        elif t.rspec["kind"] == "vm":
            result = vm.cmd(t.cmd, t.c, t.spec, t.rspec)
        else:
            print(f"unsupported kind: kind={t.rspec['kind']}")
            exit(1)
    except Exception as e:
        result = {"status": 1, "msg": colors.crit(f"{str(e)}\n{traceback.format_exc()}")}
        t.next = -1

    if t.next > 0:
        print(f"{t.cmd} node {t.rspec['name']}: next {t.next}")
    else:
        print(f"{t.cmd} node {t.rspec['name']}: completed")

        # fabricのConnectionの場合は、使い終わったら閉じる
        if type(t.c) is Connection:
            t.c.close()

    return {
        "name": t.rspec["name"],
        "result": result,
    }


def make_vm_image(t):
    print(f"{t.cmd} image {t.rspec['name']}: start")
    vm_image.cmd(t)
    print(f"{t.cmd} image {t.rspec['name']}: completed")


def trace_route(option, spec, ctx_data, tasks):
    options = option.split("_")
    srcs = options[0].split(".")
    dsts = options[1].split(".")
    src_node = spec["_node_map"][srcs[0]]
    dst_node = spec["_node_map"][dsts[0]]
    src_ip = None
    dst_ip = None
    for link in src_node.get("links", []):
        for ip in link.get("ips", []):
            src_ip = ip
            break
        if src_ip is not None:
            break
    if src_ip is None:
        for link in src_node.get("_links", []):
            for ip in link.get("peer_ips", []):
                src_ip = ip
                break
            if src_ip is not None:
                break

    for link in dst_node.get("links", []):
        for ip in link.get("ips", []):
            dst_ip = ip
            break
        if dst_ip is not None:
            break
    if dst_ip is None:
        for link in dst_node.get("_links", []):
            for ip in link.get("peer_ips", []):
                dst_ip = ip
                break
            if dst_ip is not None:
                break

    src = {
        "node": src_node,
        "ip": src_ip,
    }
    dst = {
        "node": dst_node,
        "ip": dst_ip,
    }
    rc_map = {}
    hostname_to_name = {}
    name_to_hostname = {}
    for t in tasks:
        if t.rspec["kind"] == "container":
            rc_map[t.rspec["name"]] = container_context.Context(t)
            hostname_to_name[t.rspec["_hostname"]] = t.rspec["name"]
            name_to_hostname[t.rspec["name"]] = t.rspec["_hostname"]

    _trace_route(rc_map=rc_map, src=src, dst=dst, ttl=3)
    return


def _trace_route(rc_map, src, dst, ttl):
    if ttl == 0:
        raise Exception("ttl is exceeded")
    rc = rc_map[src["name"]]
    # TODO
    rc.ip_route_get(src["ip"], dst["ip"])
    # _trace_route(rc_map, src, dst, ttl=ttl-1)
    return {}
