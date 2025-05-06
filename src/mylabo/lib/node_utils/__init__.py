import traceback

from fabric import Connection
from lib import colors

from . import container, container_context, router


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


def trace_route(t, src, dst):
    if t.rspec["kind"] != "container":
        raise Exception(f"kind={t.rspec['kind']} is not supported")
    rc = container_context.Context(t)
    node_map = rc.spec["_node_map"]
    link_map = {}
    peer_map = {}
    for rspec in node_map.values():
        vm_ovs_bridge = None
        for bridge in rspec.get("ovs", {}).get("bridges", []):
            if bridge.get("kind", "") == "vxlan-tenant-vm":
                vm_ovs_bridge = bridge["name"]
                break
        for link in rspec.get("links", []):
            link["rspec"] = rspec
            link["_rspec"] = node_map[link["peer"]]
            link["kind"] = ""
            link_map[link["link_name"]] = link
            peer_map[link["peer_name"]] = link
        for link in rspec.get("vm_links", []):
            link["rspec"] = rspec
            link["_rspec"] = node_map[link["peer"]]
            if vm_ovs_bridge is not None:
                link["vm_ovs_bridge"] = vm_ovs_bridge
            link_map[link["link_name"]] = link
            peer_map[link["peer_name"]] = link

    route = Route(rc, src, dst, link_map, peer_map, None, ttl=3)
    _trace_route(route)
    return


class Route:
    def __init__(self, rc, src, dst, link_map, peer_map, dev, ttl):
        self.rc = rc
        self.src = src
        self.dst = dst
        self.link_map = link_map
        self.peer_map = peer_map
        self.nexts = []
        self.ttl = ttl
        self.dev = dev

    def get_next_route(self, link_name):
        pair = self.get_link_pair(link_name)
        if pair is None:
            return None
        self.rc.rspec = pair["rspec"]
        return Route(self.rc, self.src, self.dst, self.link_map, self.peer_map, pair, self.ttl - 1)

    def get_link_pair(self, link_name):
        if link_name in self.link_map:
            link = self.link_map[link_name]
            return {
                "name": link["peer_name"],
                "rspec": link["_rspec"],
                "link": link,
            }
        elif link_name in self.peer_map:
            link = self.peer_map[link_name]
            return {
                "name": link["link_name"],
                "rspec": link["rspec"],
                "link": link,
            }
        else:
            return None


def _trace_route(route):
    print(f"trace_route: ttl={route.ttl}")
    if route.ttl == 0:
        return None

    routes = route.rc.ip_route_get(route.src["ip"]["ip"], route.dst["ip"]["ip"], route.dev)
    if routes is None or len(routes) == 0:
        return

    for r in routes:
        next_route = route.get_next_route(r["dev"])
        if next_route is None:
            continue
        route.nexts.append(next_route)
        _trace_route(next_route)
    return {}
