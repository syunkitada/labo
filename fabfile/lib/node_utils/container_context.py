import os
import re

re_route = re.compile("(\S+) from (\S+) dev (\S+)")


class Context:
    def __init__(self, t):
        self.c = t.c
        self.spec = t.spec
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

    def ovs_trace(self, br, flow):
        result = self.c.sudo(f"docker exec {self.rspec['_hostname']} ovs-appctl dpctl/show", hide=True, warn=True)
        port_map = {}
        for line in result.stdout.splitlines():
            splited = line.strip().split(":")
            keys = splited[0].split(" ")
            if keys[0] == "port":
                port_name = splited[1].strip().split(" ")[0]
                port_map[keys[1]] = {"name": port_name, "kind": "port"}

        result = self.c.sudo(f"docker exec {self.rspec['_hostname']} ovs-appctl ofproto/trace {br} {flow}", warn=True)
        final_flow = None
        datapath_actions = None
        for line in result.stdout.splitlines():
            if line.find("Final flow") == 0:
                final_flow = line.split("Final flow: ")[1]
            elif line.find("Datapath actions") == 0:
                datapath_actions = line.split("Datapath actions: ")[1]
        if final_flow is None or datapath_actions is None:
            return

        splited_flow = final_flow.split(",")
        flow_map = {}
        for flow in splited_flow:
            key_value = flow.split("=")
            if len(key_value) == 2:
                flow_map[key_value[0]] = key_value[1]
            else:
                flow_map[key_value[0]] = True

        actions = []
        index = 0
        brackets = 0
        for i, char in enumerate(datapath_actions):
            if char == "(":
                brackets += 1
            elif char == ")":
                brackets -= 1
            elif brackets == 0 and char == ",":
                actions.append(datapath_actions[index:i])
                index = i + 1
        else:
            actions.append(datapath_actions[index:])

        completed_actions = []
        for action in actions:
            if action.isdecimal():
                completed_actions.append(port_map[action])
            else:
                # parse action
                # ex: 'set(tunnel(tun_id=0x1388,src_ip=10.10.20.2,dst_ip=10.10.20.3,ttl=64,tp_dst_ip=4789,flags(df|key)))'
                index = 0
                arg_index = 0
                cur_action = None
                for i, char in enumerate(action):
                    if char == "(":
                        action_name = datapath_actions[index:i]
                        _action = {"name": action_name, "kind": "func", "args": []}
                        if cur_action is None:
                            cur_action = _action
                        else:
                            cur_action["args"].append(_action)
                            _action["parent_action"] = cur_action
                        cur_action = _action
                        index = i + 1
                        arg_index = i + 1
                    elif char == ")":
                        if cur_action is not None:
                            if arg_index != i:
                                splited = datapath_actions[arg_index:i].split("=")
                                if len(splited) == 2:
                                    cur_action["args"].append({"kind": "kwarg", "name": splited[0], "value": splited[1]})
                                else:
                                    cur_action["args"].append({"kind": "arg", "name": splited[0]})
                            arg_index = i + 1
                            if "parent_action" in cur_action:
                                cur_action = cur_action["parent_action"]
                    elif char == ",":
                        if cur_action is not None:
                            splited = datapath_actions[arg_index:i].split("=")
                            if len(splited) == 2:
                                cur_action["args"].append({"kind": "kwarg", "name": splited[0], "value": splited[1]})
                            else:
                                cur_action["args"].append({"kind": "arg", "name": splited[0]})
                        index = i + 1
                        arg_index = i + 1
                completed_actions.append(cur_action)

        def parse_action(flow_map, action, is_tunnel=False):
            if action["kind"] == "func":
                is_tunnel = action["name"] == "tunnel"
                for action in action.get("args", []):
                    parse_action(flow_map, action, is_tunnel)
            if is_tunnel and action["kind"] == "kwarg":
                if action["name"] == "tun_id":
                    flow_map["tun_id"] = action["value"]
                elif action["name"] == "src":
                    flow_map["tun_src"] = action["value"]
                elif action["name"] == "dst":
                    flow_map["tun_dst"] = action["value"]

        for action in completed_actions:
            parse_action(flow_map, action)

        return flow_map, completed_actions

    def ip_route_get(self, src_ip, dst_ip, dev=None):
        print("debug ip_route_get", self.rspec["_hostname"], src_ip, dst_ip)
        routes = []
        if dev is not None:
            if "vm_ovs_bridge" in dev.get("link", {}):
                result = self.c.sudo(f"docker exec {self.rspec['_hostname']} ovs-appctl dpctl/show", hide=True, warn=True)
                port_map = {}
                for line in result.stdout.splitlines():
                    splited = line.strip().split(":")
                    keys = splited[0].split(" ")
                    if keys[0] == "port":
                        port_name = splited[1].strip().split(" ")[0]
                        port_map[keys[1]] = {"name": port_name, "kind": "port"}

                br = dev["link"]["vm_ovs_bridge"]
                flow = f"in_port={dev['name']},ip,ip_src={src_ip},ip_dst={dst_ip}"
                flow_map, actions = self.ovs_trace(br, flow)
                last_action = actions[-1]
                if last_action["kind"] == "port":
                    if "tun_id" in flow_map and "tun_src" in flow_map and "tun_dst" in flow_map:
                        routes = self.ip_route_get(src_ip=flow_map["tun_src"], dst_ip=flow_map["tun_dst"])
                    else:
                        routes = self.ip_route_get(src_ip=src_ip, dst_ip=dst_ip)
                    print("debug routes", routes)
            elif dev["kind"] == "ovs_br":
                flow = f"in_port={dev['name']},ip,ip_src={src_ip},ip_dst={dst_ip}"
                result = self.c.sudo(f"docker exec {self.rspec['_hostname']} ovs-appctl ofproto/trace {dev['name']} {flow}", warn=True)
                print(result)
        else:
            result = self.c.sudo(f"docker exec {self.rspec['_hostname']} ip route get {dst_ip} from {src_ip}", hide=False, warn=True)
            if result.return_code == 0:
                for line in result.stdout.splitlines():
                    result = re_route.findall(line)
                    if len(result) == 1:
                        dev = result[0][2]
                        ovs_br = None
                        if "ovs" in self.rspec:
                            for bridge in self.rspec["ovs"]["bridges"]:
                                if dev == bridge["name"]:
                                    ovs_br = bridge
                                    break
                        if ovs_br is None:
                            routes.append(
                                {
                                    "to": result[0][0],
                                    "from": result[0][1],
                                    "dev": result[0][2],
                                }
                            )
                        else:
                            routes = self.ip_route_get(src_ip, dst_ip, dev={"name": ovs_br["name"], "kind": "ovs_br"})
        return routes
