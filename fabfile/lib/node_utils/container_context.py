import os


class Context:
    def __init__(self, t):
        self.c = t.c
        self.rspec = t.rspec
        self.debug = t.debug
        if t.ctx_data is not None:
            self.netns_map = t.ctx_data["netns_map"]
            self.docker_ps_map = t.ctx_data["docker_ps_map"]

    def dexec(self, cmd, *args, **kwargs):
        return self.c.sudo(f"docker exec {self.rspec['_hostname']} {cmd}", *args, **kwargs)

    def exec(self, cmds, title="", dryrun=False, is_local=False):
        exec_filepath = os.path.join(self.rspec["_script_dir"], f"{self.rspec['_script_index']}_{title}_exec.sh")
        full_filepath = os.path.join(self.rspec["_script_dir"], f"{self.rspec['_script_index']}_{title}_full.sh")
        log_filepath = os.path.join(self.rspec["_script_dir"], f"{self.rspec['_script_index']}_{title}.log")
        self.rspec["_script_index"] += 1

        exec_cmds = []
        full_cmds = []
        for cmd in cmds:
            if isinstance(cmd, tuple):
                if not cmd[1] and not dryrun:
                    exec_cmds.append(cmd[0])
                full_cmds.append(cmd[0])
            else:
                if not dryrun:
                    exec_cmds.append(cmd)
                full_cmds.append(cmd)

        with open(exec_filepath, "w") as f:
            if is_local:
                f.write("\n".join(exec_cmds) + "\n")
            else:
                cmds_str = "\n".join(exec_cmds)
                f.write(f"docker exec {self.rspec['_hostname']} bash -ex -c '\n{cmds_str}\n'\n")
        if len(exec_cmds) > 0:
            if self.debug:
                self.c.sudo(f"bash -c 'bash -ex {exec_filepath} 2>&1 | tee {log_filepath}'")
            else:
                self.c.sudo(f"bash -c 'bash -ex {exec_filepath} &> {log_filepath}'")

        with open(full_filepath, "w") as f:
            if is_local:
                f.write("\n".join(full_cmds))
            else:
                cmds_str = "\n".join(full_cmds)
                f.write(f"docker exec {self.rspec['_hostname']} bash -ex -c '\n{cmds_str}\n'\n")

        cmds.clear()

    def exist_netdev(self, netdev):
        return self.rspec["_hostname"] in self.netns_map and netdev in self.netns_map[self.rspec["_hostname"]]["netdev_map"]

    def exist_iprule(self, iprule):
        return self.rspec["_hostname"] in self.netns_map and iprule in self.netns_map[self.rspec["_hostname"]]["rule_map"]

    def exist_route(self, route):
        return self.rspec["_hostname"] in self.netns_map and route["dst"] in self.netns_map[self.rspec["_hostname"]]["route_map"]

    def exist_route6(self, route):
        return self.rspec["_hostname"] in self.netns_map and route["dst"] in self.netns_map[self.rspec["_hostname"]]["route6_map"]

    def append_cmds_ip_addr_add(self, cmds, ip, dev):
        if ip["version"] == 4:
            dryrun = self.exist_netdev(dev) and ip["inet"] in self.netns_map[self.rspec["_hostname"]]["netdev_map"][dev]["inet_map"]
            cmds += [(f"ip addr add {ip['inet']} dev {dev}", dryrun)]
        elif ip["version"] == 6:
            dryrun = self.exist_netdev(dev) and ip["inet"] in self.netns_map[self.rspec["_hostname"]]["netdev_map"][dev]["inet6_map"]
            cmds += [(f"ip addr add {ip['inet']} dev {dev}", dryrun)]

    def append_local_cmds_add_link(self, cmds, link):
        dryrun = self.exist_netdev(link["link_name"])
        cmds += [(f"ip link add {link['link_name']} type veth peer name {link['peer_name']}", dryrun)]

    def append_local_cmds_set_link(self, cmds, link):
        dryrun = self.exist_netdev(link["link_name"])
        cmds += [
            (f"ethtool -K {link['link_name']} tso off tx off", dryrun),
            (f"ip link set dev {link['link_name']} mtu {link['mtu']}", dryrun),
            (f"ip link set dev {link['link_name']} netns {self.rspec['_hostname']} up", dryrun),
        ]

    def append_local_cmds_set_peer(self, cmds, link):
        dryrun = self.exist_netdev(link["peer_name"])
        cmds += [
            (f"ethtool -K {link['peer_name']} tso off tx off", dryrun),
            (f"ip link set dev {link['peer_name']} mtu {link['mtu']}", dryrun),
            (f"ip link set dev {link['peer_name']} netns {self.rspec['_hostname']} up", dryrun),
        ]

    def append_cmds_add_vlan(self, cmds, netdev, vlan_id):
        netdev_vlan = f"{netdev}.{vlan_id}"
        dryrun = self.exist_netdev(netdev_vlan)
        cmds += [
            (f"ip link add link {netdev} name {netdev_vlan} type vlan id {vlan_id}", dryrun),
            (f"ip link set {netdev_vlan} up", dryrun),
        ]
