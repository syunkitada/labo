import ipaddress
import json
import re
import os


re_net_device = re.compile("^([0-9]+): ([a-zA-Z0-9-_.]+)[:@].*")
re_net_link = re.compile("link/ether ([0-9a-e:]+) ")
re_net_inet = re.compile("inet (.*/[0-9]+) ")
re_net_inet6 = re.compile("inet6 (.*/[0-9]+) ")
re_net_route = re.compile("(.*) via (.*) dev ")
re_net_rule = re.compile("([0-9]+):[ \t]+([a-z].*) lookup (.*)$")


class GlobalContext:
    def __init__(self, c, spec):
        self.c = c
        self.spec = spec

    def update_docker_ctx(self):
        docker_ps = json.loads("[" + ",".join(self.c.sudo("docker ps --format='{{json .}}'", hide=True).stdout.splitlines()) + "]")
        docker_ps_map = {}
        for ps in docker_ps:
            docker_ps_map[ps["Names"]] = ps
        self.docker_ps = docker_ps
        self.docker_ps_map = docker_ps_map

    def update_netns_ctx(self):
        netns_map = {}
        for line in self.c.sudo("ip netns", hide=True).stdout.splitlines():
            netns_name = line.split(" ")[0]
            if netns_name == "":
                continue
            netns_map[netns_name] = {
                "netdev_map": self.ip_a(netns_name),
                "route_map": self.ip_r(netns_name),
                "route6_map": self.ip_r(netns_name, isv6=True),
                "rule_map": self.ip_rule(netns_name),
            }
        self.netns_map = netns_map

    def update(self):
        self.update_docker_ctx()
        self.update_netns_ctx()

    def ip_a(self, netns=None):
        netdev_map = {}
        net = None
        cmd = "ip a"
        if netns is not None:
            cmd = f"ip netns exec {netns} {cmd}"
        for line in self.c.sudo(cmd, hide=True).stdout.splitlines():
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

    def ip_r(self, netns=None, isv6=False):
        route_map = {}
        cmd = "ip route"
        if isv6:
            cmd = "ip -6 route"
        if netns is not None:
            cmd = f"ip netns exec {netns} {cmd}"
        for line in self.c.sudo(cmd, hide=True).stdout.splitlines():
            result = re_net_route.findall(line)
            if len(result) == 1:
                route_map[result[0][0]] = {
                    "via": result[0][1],
                }
        return route_map

    def ip_rule(self, netns=None, isv6=False):
        rule_map = {}
        cmd = "ip rule"
        if isv6:
            cmd = "ip -6 rule"
        if netns is not None:
            cmd = f"ip netns exec {netns} {cmd}"
        for line in self.c.sudo(cmd, hide=True).stdout.splitlines():
            result = re_net_rule.findall(line)
            if len(result) == 1:
                rule_map[f"{result[0][1]} table {result[0][2]}"] = {
                    "prio": result[0][0],
                }
        return rule_map


class ContainerContext:
    def __init__(self, gctx, rspec):
        self.gctx = gctx
        self.rspec = rspec

    def exec(self, cmds, title="", dryrun=False, is_local=False):
        exec_filepath = os.path.join(self.rspec["_script_dir"], f"{self.rspec['_script_index']}_{title}_exec.sh")
        full_filepath = os.path.join(self.rspec["_script_dir"], f"{self.rspec['_script_index']}_{title}_full.sh")
        self.rspec["_script_index"] += 1

        exec_cmds = []
        full_cmds = []
        for cmd in cmds:
            if isinstance(cmd, tuple):
                print("cmd", cmd[0], cmd[1], dryrun)
                if not cmd[1] and not dryrun:
                    exec_cmds.append(cmd[0])
                full_cmds.append(cmd[0])
            else:
                if not dryrun:
                    exec_cmds.append(cmd)
                full_cmds.append(cmd)

        with open(exec_filepath, "w") as f:
            if is_local:
                f.write("\n".join(exec_cmds))
            else:
                cmds_str = "\n".join(exec_cmds)
                f.write(f"docker exec {self.rspec['_hostname']} bash -ex -c '\n{cmds_str}'\n")
        if len(exec_cmds) > 0:
            self.gctx.c.sudo(f"bash -ex {exec_filepath}")

        with open(full_filepath, "w") as f:
            if is_local:
                f.write("\n".join(full_cmds))
            else:
                cmds_str = "\n".join(full_cmds)
                f.write(f"docker exec {self.rspec['_hostname']} bash -ex -c '\n{cmds_str}\n'\n")

        cmds.clear()

    def exist_netdev(self, netdev):
        return self.rspec["_hostname"] in self.gctx.netns_map and netdev in self.gctx.netns_map[self.rspec["_hostname"]]["netdev_map"]

    def exist_iprule(self, iprule):
        return self.rspec["_hostname"] in self.gctx.netns_map and iprule in self.gctx.netns_map[self.rspec["_hostname"]]["rule_map"]

    def exist_route(self, route):
        return self.rspec["_hostname"] in self.gctx.netns_map and route["dst"] in self.gctx.netns_map[self.rspec["_hostname"]]["route_map"]

    def exist_route6(self, route):
        return self.rspec["_hostname"] in self.gctx.netns_map and route["dst"] in self.gctx.netns_map[self.rspec["_hostname"]]["route6_map"]
