import ipaddress
import re


re_net_device = re.compile("^([0-9]+): ([a-zA-Z0-9-_.]+)[:@].*")
re_net_link = re.compile("link/ether ([0-9a-e:]+) ")
re_net_inet = re.compile("inet (.*/[0-9]+) ")
re_net_inet6 = re.compile("inet6 (.*/[0-9]+) ")
re_net_route = re.compile("(.*) via (.*) dev ")
re_net_rule = re.compile("([0-9]+):[ \t]+([a-z].*) lookup (.*)$")


def get_netns_map(c):
    netns_map = {}
    for line in c.sudo("ip netns", hide=True).stdout.splitlines():
        netns_name = line.split(" ")[0]
        if netns_name == "":
            continue
        netns_map[netns_name] = {
            "netdev_map": ip_a(c, netns_name),
            "route_map": ip_r(c, netns_name),
            "route6_map": ip_r(c, netns_name, isv6=True),
            "rule_map": ip_rule(c, netns_name),
        }
    return netns_map


def ip_a(c, netns=None):
    netdev_map = {}
    net = None
    cmd = "ip a"
    if netns is not None:
        cmd = f"ip netns exec {netns} {cmd}"
    for line in c.sudo(cmd, hide=True).stdout.splitlines():
        result = re_net_device.findall(line)
        if len(result) == 1:
            if net is not None:
                netdev_map[net["name"]] = net
            net = {
                "name": result[0][1],
                "inet_map": {},
                "inet6_map": {},
            }
            continue
        result = re_net_link.findall(line)
        if len(result) == 1:
            if net is not None:
                net["mac"] = result[0]
            continue
        result = re_net_inet.findall(line)
        if len(result) == 1:
            if net is not None:
                net["inet_map"][result[0]] = {}
            continue
        result = re_net_inet6.findall(line)
        if len(result) == 1:
            if net is not None:
                ip_interface = ipaddress.ip_interface(result[0])
                net["inet6_map"][ip_interface.exploded] = {}
            continue
    else:
        if net is not None:
            netdev_map[net["name"]] = net

    return netdev_map


def ip_r(c, netns=None, isv6=False):
    route_map = {}
    cmd = "ip route"
    if isv6:
        cmd = "ip -6 route"
    if netns is not None:
        cmd = f"ip netns exec {netns} {cmd}"
    for line in c.sudo(cmd, hide=True).stdout.splitlines():
        result = re_net_route.findall(line)
        if len(result) == 1:
            route_map[result[0][0]] = {
                "via": result[0][1],
            }
    return route_map


def ip_rule(c, netns=None, isv6=False):
    rule_map = {}
    cmd = "ip rule"
    if isv6:
        cmd = "ip -6 rule"
    if netns is not None:
        cmd = f"ip netns exec {netns} {cmd}"
    for line in c.sudo(cmd, hide=True).stdout.splitlines():
        result = re_net_rule.findall(line)
        if len(result) == 1:
            rule_map[f"{result[0][1]} table {result[0][2]}"] = {
                "prio": result[0][0],
            }
    return rule_map
