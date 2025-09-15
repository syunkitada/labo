import logging
import json

from mylabo.domain import resource
from mylabo.lib.runtime import node_context
from mylabo.lib.context import context

LOG = logging.getLogger(__name__)


class Container(resource.Resource):
    def __init__(self, ctx: context.Context, manifest: dict):
        self.ctx = ctx
        self.c = node_context.NodeContext(manifest)
        self.manifest = manifest
        self.spec = manifest["spec"]
        self.next = 0

    def get(self):
        cmd = f"docker inspect {self.manifest['_hostname']}"
        result = self.c.exec_without_log(cmd, is_local=True, hide=True)
        containers = json.loads(result.stdout)
        container = containers[0]
        return {
            "name": self.manifest["name"],
            "id": container["Name"],
            "status": container.get("State", {}).get("Status", "unknown"),
        }

    def apply(self):
        print("apply container\n\n", self.manifest)
        if self.next == 0:
            self._apply_prepare()
            self.next = 1
        elif self.next == 1:
            self._apply()
            self.next = -1

    def delete(self):
        self.c.c.sudo(f"docker kill {self.manifest['_hostname']}", hide=True, warn=True)
        self.c.c.sudo(f"rm -rf /var/run/netns/{self.manifest['_hostname']}", hide=True)

        for link in self.spec.get("_links", []):
            self.c.c.sudo(f"ip link del {link['link_name']}", warn=True)

    def test(self):
        for tt in self.spec.get("tests", []):
            self.c.run_module(tt)

    def any(self, action: resource.AnyAction):
        pass

    def _apply_prepare(self):
        lcmds = []
        for link in self.spec.get("links", []):
            self.c.append_local_cmds_add_link(lcmds, link)
        self.c.exec(lcmds, title="prepare-links", is_local=True)

        # メモ: (負荷が高いと？)dockerでsystemdが起動できないことがある
        docker_options = [
            f"-d  --rm --network {self.manifest['spec'].get('network', 'none')} --privileged --name {self.manifest['_hostname']}",
            "-v /mnt/nfs:/mnt/nfs:ro",
            f"-v {self.c.script_dir}:{self.c.script_dir}",
        ]

        cgroup = self.c.c.sudo("stat -fc %T /sys/fs/cgroup/").stdout
        if cgroup == "tmpfs":
            docker_options += [
                "--cap-add=SYS_ADMIN",
                "-v /sys/fs/cgroup:/sys/fs/cgroup:rw",
                "--cgroupns host",
            ]
        elif cgroup == "cgroup2fs":
            docker_options += [
                "--cap-add=SYS_ADMIN",
                "--cgroup-parent docker.slice",
                "--cgroupns private",
            ]

        for port in self.spec.get("ports", []):
            docker_options += [f"-p {port}"]

        lcmds = [
            f"if ! docker inspect {self.manifest['_hostname']}; then",
            f"docker run {' '.join(docker_options)} {self.manifest['spec']['image']}",
            f"pid=`docker inspect {self.manifest['_hostname']}" + " --format '{{.State.Pid}}'`",
            "ln -sfT /proc/${pid}/ns/net " + f"/var/run/netns/{self.manifest['_hostname']}",
            "fi",
        ]
        self.c.exec(lcmds, title="prepare-docker", is_local=True)

        lcmds = []
        for route in self.spec.get("local_routes", []):
            lcmds += [
                "ipaddr=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "
                + self.manifest["_hostname"]
                + ")",
            ]
            self.c.append_cmds_ip_route_add(lcmds, route["dst"], "${ipaddr}")
        self.c.exec(lcmds, title="local_routes", is_local=True)

    def _apply(self):
        skipped = False

        lcmds = []
        dcmds = []
        dcmds += [f"hostname {self.manifest['_hostname']}"]
        for key, value in self.spec.get("sysctl_map", {}).items():
            dcmds += [f"sysctl -w {key}={value}"]
        for bridge in self.spec.get("bridges", []):
            dcmds += [
                f"if ! ip addr show {bridge['name']}; then",
                f"  ip link add {bridge['name']} type bridge",
                f"  ip link set {bridge['name']} up",
                f"  ip link set dev {bridge['name']} mtu {bridge['mtu']}",
                "fi",
            ]
            for ip in bridge.get("ips", []):
                self.c.append_cmds_ip_addr_add(dcmds, ip, bridge["name"])
        self.c.exec(dcmds, title="init-docker")

        for link in self.spec.get("links", []):
            if link["kind"] == "veth":
                self.c.append_local_cmds_set_link(lcmds, link)
            elif link["kind"] == "tap":
                self.c.append_local_cmds_set_peer(lcmds, link)
        for link in self.spec.get("_links", []):
            self.c.append_local_cmds_set_peer(lcmds, link)
        self.c.exec(lcmds, title="prepare-links", is_local=True)

        for link in self.spec.get("links", []):
            for vlan_id, _ in link.get("vlan_map", {}).items():
                self.c.append_cmds_add_vlan(dcmds, link["link_name"], vlan_id)
            if "bridge" in link:
                if link["kind"] == "veth":
                    dcmds += [
                        f"ip link set dev {link['link_name']} master {link['bridge']}",
                    ]
                elif link["kind"] == "tap":
                    dcmds += [
                        f"ip link set dev {link['peer_name']} master {link['bridge']}",
                    ]
        for link in self.spec.get("_links", []):
            for vlan_id, _ in link.get("vlan_map", {}).items():
                self.c.append_cmds_add_vlan(dcmds, link["peer_name"], vlan_id)

        # ip_addr_add
        for ip in self.spec.get("lo_ips", []):
            self.c.append_cmds_ip_addr_add(dcmds, ip, "lo")
        for link in self.spec.get("links", []):
            for ip in link.get("ips", []):
                self.c.append_cmds_ip_addr_add(dcmds, ip, link["link_name"])
        for link in self.spec.get("_links", []):
            for ip in link.get("peer_ips", []):
                self.c.append_cmds_ip_addr_add(dcmds, ip, link["peer_name"])
        if "sid" in self.spec:
            self.c.append_cmds_ip_addr_add(dcmds, self.spec["sid"], self.spec["sid"]["dev"])

        for iprule in self.spec.get("ip_rules", []):
            dcmds += self.c.wrap_if_exist_iprule(
                iprule["rule"], [f"ip rule add {iprule['rule']} prio {iprule['prio']}"]
            )

        for route in self.spec.get("routes", []):
            self.c.append_cmds_ip_route_add(dcmds, route["dst"], route["via"])
        for route in self.spec.get("routes6", []):
            skipped = self.c.exist_route6(route)
            dcmds += [(f"ip -6 route add {route['dst']} via {route['via']}", skipped)]

        self.c.exec(dcmds, title="setup-networks")

        l3admin = self.spec.get("l3admin")
        if l3admin is not None:
            dcmds += self.c.wrap_if_exist_netdev(
                "l3admin",
                [
                    "ip link add l3admin type dummy",
                    "ip link set up l3admin",
                ],
            )

            iprule = "from all table 300"
            dcmds += self.c.wrap_if_exist_iprule(iprule, [f"ip rule add {iprule} prio 30"])

            for ip in l3admin.get("ips", []):
                self.c.append_cmds_ip_addr_add(dcmds, ip, "l3admin")

            routes = []
            for link in self.spec.get("_links", []):
                for vlan_id, vlan in link.get("vlan_map", {}).items():
                    if vlan.get("bgp_peer_group", "") == "ADMIN":
                        dcmds += [
                            # frrが以下の設定を入れてくれるので、169.254.0.1をgatewayとして使える
                            # 169.254.0.1 dev HV1_0_L11.100 lladdr 5e:de:b2:b4:98:4f PERMANENT proto zebra
                            # ルートを設定するために、仮で169.254.0.2/24を各インターフェイスに付ける
                            f"ip addr show {link['peer_name']}.{vlan_id} | grep 169.254.0.2/24"
                            + f" || ip addr add 169.254.0.2/24 dev {link['peer_name']}.{vlan_id}",
                        ]
                        routes += [f"nexthop via 169.254.0.1 dev {link['peer_name']}.{vlan_id}"]
            if len(routes) > 0:
                for ip in l3admin.get("ips", []):
                    if ip["version"] == 4:
                        dcmds += [f"ip route replace table 300 0.0.0.0/0 src {ip['ip']} {' '.join(routes)}"]
            self.c.exec(dcmds, title="setup-l3admin")

        for step in self.spec.get("steps", []):
            self.c.run_module(step)
