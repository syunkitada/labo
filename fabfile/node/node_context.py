from lib.runtime import runtime_context
import os
import re
import yaml as pyyaml
from lib import colors

re_route = re.compile("(\S+) from (\S+) dev (\S+)")


class NodeContext:
    def __init__(self, spec, cmd, rspec, debug, dryrun):
        self.c = runtime_context.new(spec)
        self.cmd = cmd
        self.spec = spec
        self.rspec = rspec
        self.next = 0
        self.debug = debug
        self.dryrun = dryrun
        self.full_cmds = []
        self.childs = []

    def _cmd(self, exec_filepath, log_filepath=None, is_local=False):
        cmd = ""
        if log_filepath is None:
                cmd = f"bash -ex {exec_filepath}"
        else:
            if self.debug:
                cmd = f"bash -ex {exec_filepath} 2>&1 | tee {log_filepath}"
            else:
                cmd = f"bash -ex {exec_filepath} &> {log_filepath}"

        if is_local:
            return f"PATH={os.environ['PATH']} {cmd}"
        elif self.rspec["kind"] == "container":
            return f"docker exec {self.rspec['_hostname']} {cmd}"
        elif self.rspec["kind"] == "vm":
            return f"ssh -i /root/.ssh/labo.pem admin@{self.rspec['_hostname']} sudo {cmd}"
        return cmd

    def exec_without_log(self, cmd, *args, is_local=False, **kwargs):
        tmp_cmd = ""
        if is_local:
            tmp_cmd = f"PATH={os.environ['PATH']} {cmd}"
        elif self.rspec["kind"] == "container":
            tmp_cmd = f"docker exec {self.rspec['_hostname']} {cmd}"
        elif self.rspec["kind"] == "vm":
            tmp_cmd = f"ssh -i /root/.ssh/labo.pem admin@{self.rspec['_hostname']} sudo {cmd}"
        return self.c.sudo(tmp_cmd, *args, **kwargs)

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

        if len(exec_cmds) > 0:
            with open(exec_filepath, "w") as f:
                cmds_str = "\n".join(exec_cmds) + "\n"
                f.write(cmds_str)

            if not self.dryrun:
                self.c.sudo(self._cmd(exec_filepath, log_filepath, is_local))
            else:
                print(f"skipped exec {exec_filepath}, because of dryrun mode")

        with open(full_filepath, "w") as f:
            full_cmds_str = "\n".join(full_cmds) + "\n"
            f.write(full_cmds_str)

        cmd = self._cmd(full_filepath, None, is_local)
        self.full_cmds += [
            f"# {self.rspec['name']}: {comment_name_prefix} {'-'*(80-len(comment_name_prefix))}",
            cmd,
            "",
        ]

        cmds.clear()

    def write(self, file_path, txt=None, yaml=None, is_local=False):
        if yaml is not None:
            txt = pyyaml.dump(yaml, default_flow_style=False)
        if txt is None:
            raise Exception("txt is None")
        if is_local:
            with open(file_path, "w") as f:
                f.write(txt)
        else:
            if file_path[0] != "/":
                raise Exception("invalid file_path: {file_path}")
            tmp_file_path = os.path.join(self.rspec["_script_dir"], file_path[1:])
            os.makedirs(os.path.dirname(tmp_file_path), exist_ok=True)
            with open(tmp_file_path, "w") as f:
                f.write(txt)
            cmds = [
                f"mkdir -p {os.path.dirname(file_path)}",
                f"cp {tmp_file_path} {file_path}",
            ]
            self.exec(cmds)

    def exist_netdev(self, netdev):
        return self.rspec["_hostname"] in self.netns_map and netdev in self.netns_map[self.rspec["_hostname"]]["netdev_map"]

    def exist_iprule(self, iprule):
        return self.rspec["_hostname"] in self.netns_map and iprule in self.netns_map[self.rspec["_hostname"]]["rule_map"]

    def exist_route(self, route):
        return self.rspec["_hostname"] in self.netns_map and route["dst"] in self.netns_map[self.rspec["_hostname"]]["route_map"]

    def exist_route6(self, route):
        return self.rspec["_hostname"] in self.netns_map and route["dst"] in self.netns_map[self.rspec["_hostname"]]["route6_map"]

    def append_cmds_ip_route_add(self, cmds, dst, via):
        cmds += [
            'set +e',
            f'exists_route=$(ip route | grep {dst})',
            'set -e',
            f'expected_route="{dst} via {via}"',
            'if [ "${exists_route}" != "" ]; then',
            'if [ "${exists_route}" != "${expected_route}" ]; then',
            'ip route del $exists_route',
            f'ip route add {dst} via {via}',
            'fi',
            'else',
            f'ip route add {dst} via {via}',
            'fi',
        ]

    def append_cmds_ip_addr_add(self, cmds, ip, dev):
        if ip["version"] == 4:
            cmds += [
                f"if ! ip addr show dev {dev} | grep 'inet {ip['inet']}'; then",
                f"ip addr add {ip['inet']} dev {dev}",
                "fi",
            ]
        elif ip["version"] == 6:
            cmds += [
                f"if ! ip addr show dev {dev} | grep 'inet6 {ip['inet']}'; then",
                f"ip addr add {ip['inet']} dev {dev}",
                "fi",
            ]

    def append_local_cmds_add_link(self, cmds, link):
        if link["kind"] != "veth":
            return
        skipped = self.exist_netdev(link["link_name"])
        cmds += [(f"ip link add {link['link_name']} type veth peer name {link['peer_name']}", skipped)]

    def append_local_cmds_set_link(self, cmds, link):
        cmds += [
            f"if ! ip netns exec {self.rspec['_hostname']} ip addr show dev {link['link_name']}; then",
            f"ethtool -K {link['link_name']} tso off tx off",
            f"ip link set dev {link['link_name']} mtu {link['mtu']}",
            f"ip link set dev {link['link_name']} address {link['link_mac']}",
            f"ip link set dev {link['link_name']} netns {self.rspec['_hostname']} up",
            "fi",
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

    def ansible(self, ansible):
        self.write("/etc/ansible/vars.yaml", pyyaml.dump(ansible['vars']))
        cmds = [
            "export PATH=$PATH:/usr/local/bin",
            "export LANG=C.UTF-8",
            "export LC_ALL=en_US.UTF-8",
        ]
        for play in ansible.get("plays", []):
            cmds += [
                f"ansible-playbook /mnt/nfs/labo/ansible/playbooks/{play}/main.yaml",
            ]
        self.exec(cmds)
