import os
import re
import yaml as pyyaml
from jinja2 import Template

from mylabo.lib.runtime import runtime_context
from mylabo.lib import colors

re_route = re.compile("(\S+) from (\S+) dev (\S+)")


class NodeContext:
    def __init__(self, spec):
        self.c = runtime_context.new(spec)
        self.spec = spec
        self.next = 0
        self.debug = False
        self.dryrun = False
        self.full_cmds = []
        self.childs = []

        self.script_dir = os.path.join(spec["_root_spec"]["_script_dir"], spec["name"])
        self.script_index = 0
        os.makedirs(self.script_dir, exist_ok=True)

    def _cmd(self, exec_filepath, is_local=False):
        cmd = f"bash -ex {exec_filepath}"

        if is_local:
            return f"PATH={os.environ['PATH']} {cmd}"
        elif self.spec["kind"] == "container":
            return f"docker exec {self.spec['_hostname']} {cmd}"
        elif self.spec["kind"] == "vm":
            return f"ssh -i /root/.ssh/labo.pem admin@{self.spec['_hostname']} sudo {cmd}"
        return cmd

    def exec_without_log(self, cmd: str, *args, is_local=False, **kwargs):
        tmp_cmd = ""
        if is_local:
            tmp_cmd = f"PATH={os.environ['PATH']} {cmd}"
        elif self.spec["kind"] == "container":
            tmp_cmd = f"docker exec {self.spec['_hostname']} {cmd}"
        elif self.spec["kind"] == "vm":
            tmp_cmd = f"ssh -i /root/.ssh/labo.pem admin@{self.spec['_hostname']} sudo {cmd}"

        # Remove unsupported parameters for invoke library
        kwargs.pop("title", None)

        return self.c.sudo(tmp_cmd, *args, **kwargs)

    def exec(self, cmds, title=None, skipped=False, is_local=False):
        file_name_prefix = ""
        comment_name_prefix = ""
        if title is None:
            file_name_prefix = f"{self.script_index}"
            comment_name_prefix = f"{self.script_index}"
        else:
            file_name_prefix = f"{self.script_index}_{title.replace(' ', '-').replace('/', '-')}"
            comment_name_prefix = f"{self.script_index}: {title}"

        exec_filepath = os.path.join(self.script_dir, f"{file_name_prefix}_exec.sh")
        full_filepath = os.path.join(self.script_dir, f"{file_name_prefix}_full.sh")
        log_filepath = os.path.join(self.script_dir, f"{file_name_prefix}.log")
        self.script_index += 1

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
                result = self.c.sudo(self._cmd(exec_filepath, is_local))
                with open(log_filepath, "w") as f:
                    f.write(result.stdout)
                if self.debug:
                    print(result.stdout)
            else:
                print(f"skipped exec {exec_filepath}, because of dryrun mode")

        with open(full_filepath, "w") as f:
            full_cmds_str = "\n".join(full_cmds) + "\n"
            f.write(full_cmds_str)

        cmd = self._cmd(full_filepath, is_local)
        self.full_cmds += [
            f"# {self.spec['name']}: {comment_name_prefix} {'-'*(80-len(comment_name_prefix))}",
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
            tmp_file_path = os.path.join(self.script_dir, file_path[1:])
            os.makedirs(os.path.dirname(tmp_file_path), exist_ok=True)
            with open(tmp_file_path, "w") as f:
                f.write(txt)
            cmds = [
                f"ls {self.script_dir}",
                f"mkdir -p {os.path.dirname(file_path)}",
                f"cp {tmp_file_path} {file_path}",
            ]
            self.exec(cmds)

    def wrap_if_exist_netdev_netns(self, netdev, cmds):
        cmds.insert(0, f"if ! ip netns exec {self.spec['_hostname']} ip addr show dev {netdev}; then")
        cmds.append("fi")
        return cmds

    def wrap_if_exist_netdev(self, netdev, cmds):
        cmds.insert(0, f"if ! ip addr show dev {netdev}; then")
        cmds.append("fi")
        return cmds

    def wrap_if_exist_iprule(self, iprule, cmds):
        cmds.insert(0, f"if ! ip rule | sed -e 's/lookup/table/g' | grep '{iprule}'; then")
        cmds.append("fi")
        return cmds

    def exist_route(self, route):
        return (
            self.spec["_hostname"] in self.netns_map
            and route["dst"] in self.netns_map[self.spec["_hostname"]]["route_map"]
        )

    def exist_route6(self, route):
        return (
            self.spec["_hostname"] in self.netns_map
            and route["dst"] in self.netns_map[self.spec["_hostname"]]["route6_map"]
        )

    def append_cmds_ip_route_add(self, cmds, dst, via):
        cmds += [
            "set +e",
            f'exists_routes=$(ip route | grep {dst} | awk \'{{print $1" "$2" "$3}}\')',
            "set -e",
            f'expected_route="{dst} via {via}"',
            "exists_expected_route=0",
            "IFS='\n'",
            "for exists_route in $exists_routes; do",
            '  if [ "${exists_route}" != "" ]; then',
            '    if [ "${exists_route}" != "${expected_route}" ]; then',
            '      sh -c "ip route del $exists_route"',
            "    fi",
            '    if [ "${exists_route}" == "${expected_route}" ]; then',
            "      exists_expected_route=1",
            "    fi",
            "  fi",
            "done",
            "if [ $exists_expected_route -eq 0 ]; then",
            f"  ip route add {dst} via {via}",
            "fi",
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
                f"if ! ip addr show dev {dev} | grep 'inet6 {ip['inet_compressed']}'; then",
                f"ip addr add {ip['inet']} dev {dev}",
                "fi",
            ]

    def append_local_cmds_add_link(self, cmds, link):
        if link["kind"] != "veth":
            return

        cmds += self.wrap_if_exist_netdev_netns(
            link["link_name"],
            [
                f"if ! ip link show dev {link['link_name']}; then",
                f"ip link add {link['link_name']} type veth peer name {link['peer_name']}",
                "fi",
            ],
        )

    def append_local_cmds_set_link(self, cmds, link):
        cmds += self.wrap_if_exist_netdev_netns(
            link["link_name"],
            [
                f"ethtool -K {link['link_name']} tso off tx off",
                f"ip link set dev {link['link_name']} mtu {link['mtu']}",
                f"ip link set dev {link['link_name']} address {link['link_mac']}",
                f"ip link set dev {link['link_name']} netns {self.spec['_hostname']} up",
            ],
        )

    def append_local_cmds_set_peer(self, cmds, link):
        cmds += self.wrap_if_exist_netdev_netns(
            link["peer_name"],
            [
                f"ethtool -K {link['peer_name']} tso off tx off",
                f"ip link set dev {link['peer_name']} mtu {link['mtu']}",
                f"ip link set dev {link['peer_name']} address {link['peer_mac']}",
                f"ip link set dev {link['peer_name']} netns {self.spec['_hostname']} up",
            ],
        )

    def append_cmds_add_vlan(self, cmds, netdev, vlan_id):
        netdev_vlan = f"{netdev}.{vlan_id}"
        cmds += self.wrap_if_exist_netdev(
            netdev_vlan,
            [
                f"ip link add link {netdev} name {netdev_vlan} type vlan id {vlan_id}",
                f"ip link set {netdev_vlan} up",
            ],
        )

    def run_module(self, module: dict):
        if "shell" in module:
            self.shell(module["shell"], title=module.get("title", "shell"))
        elif "template" in module:
            self.template(module["template"], title=module.get("title", "template"))

    def shell(self, shell: dict, title: str):
        self.exec(shell["cmds"], title=title)

    def template(self, template: dict, title: str):
        template_file = os.path.join(self.spec["_root_spec"]["_spec_dir"], template["src"])
        with open(template_file) as f:
            content = f.read()
            t = Template(content)
            rendered = t.render(node=self.spec, spec=self.spec["spec"])

        dst_file = os.path.join(self.script_dir, template["src"])
        dst_dir = os.path.dirname(os.path.realpath(dst_file))
        os.makedirs(dst_dir, exist_ok=True)
        with open(dst_file, "w") as f:
            f.write(rendered)

        cmds = [
            f"cp {dst_file} {template['dst']}",
        ]
        self.exec(cmds, title=title)
