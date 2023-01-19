import os


class Context:
    def __init__(self, t):
        self.c = t.c
        self.rspec = t.rspec
        self.debug = t.debug
        self.dryrun = t.dryrun
        self.full_cmds = []
        if t.ctx_data is not None:
            self.netns_map = t.ctx_data["netns_map"]
            self.docker_ps_map = t.ctx_data["docker_ps_map"]

    def dexec(self, cmd, *args, **kwargs):
        return self.c.sudo(f"docker exec {self.rspec['_hostname']} {cmd}", *args, **kwargs)

    def exec(self, cmds, title=None, skipped=False, is_local=False):
        file_name_prefix = ""
        comment_name_prefix = ""
        if title is None:
            file_name_prefix = f"{self.rspec['_script_index']}"
            comment_name_prefix = f"{self.rspec['_script_index']}"
        else:
            file_name_prefix = f"{self.rspec['_script_index']}_{title.replace(' ', '-')}"
            comment_name_prefix = f"{self.rspec['_script_index']}: {title}"

        exec_filepath = os.path.join(self.rspec["_script_dir"], f"{file_name_prefix}_exec.sh")
        full_filepath = os.path.join(self.rspec["_script_dir"], f"{file_name_prefix}_full.sh")
        log_filepath = os.path.join(self.rspec["_script_dir"], f"{file_name_prefix}.log")
        self.rspec["_script_index"] += 1

        exec_cmds = []
        full_cmds = []
        for cmd in cmds:
            if isinstance(cmd, tuple):
                if not cmd[1] and not skipped:
                    exec_cmds.append(cmd[0])
                full_cmds.append(cmd[0])
            else:
                if not skipped:
                    exec_cmds.append(cmd)
                full_cmds.append(cmd)

        with open(exec_filepath, "w") as f:
            cmds_str = "\n".join(exec_cmds) + "\n"
            if not is_local:
                cmds_str = f"docker exec {self.rspec['_hostname']} bash -ex -c '\n{cmds_str}'\n"
            f.write(cmds_str)

        if len(exec_cmds) > 0:
            if not self.dryrun:
                if self.debug:
                    self.c.sudo(f"bash -c 'bash -ex {exec_filepath} 2>&1 | tee {log_filepath}'")
                else:
                    self.c.sudo(f"bash -c 'bash -ex {exec_filepath} &> {log_filepath}'")
            else:
                print(f"skipped exec {exec_filepath}, because of dryrun mode")

        with open(full_filepath, "w") as f:
            full_cmds_str = "\n".join(full_cmds) + "\n"
            if not is_local:
                full_cmds_str = f"docker exec {self.rspec['_hostname']} bash -ex -c '\n{full_cmds_str}'\n"
            f.write(full_cmds_str)

        self.full_cmds += [
            f"# {self.rspec['name']}: {comment_name_prefix} {'-'*(80-len(comment_name_prefix))}",
            full_cmds_str,
            "",
        ]

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
            skipped = self.exist_netdev(dev) and ip["inet"] in self.netns_map[self.rspec["_hostname"]]["netdev_map"][dev]["inet_map"]
            cmds += [(f"ip addr add {ip['inet']} dev {dev}", skipped)]
        elif ip["version"] == 6:
            skipped = self.exist_netdev(dev) and ip["inet"] in self.netns_map[self.rspec["_hostname"]]["netdev_map"][dev]["inet6_map"]
            cmds += [(f"ip addr add {ip['inet']} dev {dev}", skipped)]

    def append_local_cmds_add_link(self, cmds, link):
        skipped = self.exist_netdev(link["link_name"])
        cmds += [(f"ip link add {link['link_name']} type veth peer name {link['peer_name']}", skipped)]

    def append_local_cmds_set_link(self, cmds, link):
        skipped = self.exist_netdev(link["link_name"])
        cmds += [
            (f"ethtool -K {link['link_name']} tso off tx off", skipped),
            (f"ip link set dev {link['link_name']} mtu {link['mtu']}", skipped),
            (f"ip link set dev {link['link_name']} address {link['link_mac']}", skipped),
            (f"ip link set dev {link['link_name']} netns {self.rspec['_hostname']} up", skipped),
        ]

    def append_local_cmds_set_peer(self, cmds, link):
        skipped = self.exist_netdev(link["peer_name"])
        cmds += [
            (f"ethtool -K {link['peer_name']} tso off tx off", skipped),
            (f"ip link set dev {link['peer_name']} mtu {link['mtu']}", skipped),
            (f"ip link set dev {link['peer_name']} address {link['peer_mac']}", skipped),
            (f"ip link set dev {link['peer_name']} netns {self.rspec['_hostname']} up", skipped),
        ]

    def append_cmds_add_vlan(self, cmds, netdev, vlan_id):
        netdev_vlan = f"{netdev}.{vlan_id}"
        skipped = self.exist_netdev(netdev_vlan)
        cmds += [
            (f"ip link add link {netdev} name {netdev_vlan} type vlan id {vlan_id}", skipped),
            (f"ip link set {netdev_vlan} up", skipped),
        ]

    def ip_route_get(self, src, dst):
        result = self.c.sudo(f"docker exec -it {self.rspec['_hostname']} ip route get {dst} from {src}")
        # TODO: parse 10.100.0.3 from 10.100.0.2 dev t1vm1_0_HV1 uid 0
