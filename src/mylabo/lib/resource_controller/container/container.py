import os
import logging

from mylabo.domain import resource
from mylabo.lib.runtime import node_context

LOG = logging.getLogger(__name__)


class Container(resource.Resource):
    def __init__(self, spec):
        self.spec = spec
        self.c = node_context.NodeContext(spec)
        self.next = 0
        spec["_hostname"] = f"{spec['_root_spec']['namespace']}-{spec['name']}"

    def get(self):
        print("get")

    def apply(self):
        print("apply container\n\n", self.spec)
        if self.next == 0:
            self._apply_prepare()
            self.next = 1
        elif self.next == 1:
            self._apply()
            self.next = -1

    def delete(self):
        print("delete container\n\n", self.spec)

    def _apply_prepare(self):
        spec = self.spec["spec"]

        lcmds = []
        for link in spec.get("links", []):
            self.c.append_local_cmds_add_link(lcmds, link)
        for link in spec.get("child_links", []):
            self.c.append_local_cmds_add_link(lcmds, link)
        self.c.exec(lcmds, title="prepare-links", is_local=True)

        # メモ: (負荷が高いと？)dockerでsystemdが起動できないことがある
        docker_options = [
            f"-d  --rm --network {spec.get('network', 'none')} --privileged --name {self.spec['_hostname']}",
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

        for port in spec.get("ports", []):
            docker_options += [f"-p {port}"]

        lcmds = [
            f"if ! docker inspect {self.spec['_hostname']}; then",
            f"docker run {' '.join(docker_options)} {spec['image']}",
            f"pid=`docker inspect {self.spec['_hostname']}" + " --format '{{.State.Pid}}'`",
            "ln -sfT /proc/${pid}/ns/net " + f"/var/run/netns/{self.spec['_hostname']}",
            "fi",
        ]
        self.c.exec(lcmds, title="prepare-docker", is_local=True)

        lcmds = []
        for route in spec.get("local_routes", []):
            lcmds += [
                "ipaddr=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "
                + self.spec["_hostname"]
                + ")",
            ]
            self.c.append_cmds_ip_route_add(lcmds, route["dst"], "${ipaddr}")
        self.c.exec(lcmds, title="local_routes", is_local=True)

    def _apply(self):
        spec = self.spec["spec"]

        skipped = False

        lcmds = []
        dcmds = []
        dcmds += [f"hostname {self.spec['_hostname']}"]
        for key, value in spec.get("sysctl_map", {}).items():
            dcmds += [f"sysctl -w {key}={value}"]
        for bridge in spec.get("bridges", []):
            dcmds += [
                f"if ! ip addr show {bridge['name']}; then",
                f"ip link add {bridge['name']} type bridge",
                f"ip link set {bridge['name']} up",
                f"ip link set dev {bridge['name']} mtu {bridge['mtu']}",
                "fi",
            ]
            for ip in bridge.get("ips", []):
                self.c.append_cmds_ip_addr_add(dcmds, ip, bridge["name"])
        self.c.exec(dcmds, title="init-docker")

        for link in spec.get("links", []):
            self.c.append_local_cmds_set_link(lcmds, link)
        for link in spec.get("_links", []):
            self.c.append_local_cmds_set_peer(lcmds, link)
        for link in spec.get("child_links", []):
            self.c.append_local_cmds_set_link(lcmds, link)
        self.c.exec(lcmds, title="prepare-links", is_local=True)

        for link in spec.get("links", []):
            for vlan_id, _ in link.get("vlan_map", {}).items():
                self.c.append_cmds_add_vlan(dcmds, link["link_name"], vlan_id)
            if "bridge" in link:
                dcmds += [
                    f"ip link set dev {link['link_name']} master {link['bridge']}",
                ]
        for link in spec.get("_links", []):
            for vlan_id, _ in link.get("vlan_map", {}).items():
                self.c.append_cmds_add_vlan(dcmds, link["peer_name"], vlan_id)

        for ip in spec.get("lo_ips", []):
            self.c.append_cmds_ip_addr_add(dcmds, ip, "lo")
        for link in spec.get("links", []):
            for ip in link.get("ips", []):
                self.c.append_cmds_ip_addr_add(dcmds, ip, link["link_name"])
        for link in spec.get("_links", []):
            for ip in link.get("peer_ips", []):
                self.c.append_cmds_ip_addr_add(dcmds, ip, link["peer_name"])
        if "sid" in spec:
            self.c.append_cmds_ip_addr_add(dcmds, spec["sid"], spec["sid"]["dev"])

        for iprule in spec.get("ip_rules", []):
            dcmds += self.c.wrap_if_exist_iprule(
                iprule["rule"], [f"ip rule add {iprule['rule']} prio {iprule['prio']}"]
            )

        for route in spec.get("routes", []):
            self.c.append_cmds_ip_route_add(dcmds, route["dst"], route["via"])
        for route in spec.get("routes6", []):
            skipped = self.c.exist_route6(route)
            dcmds += [(f"ip -6 route add {route['dst']} via {route['via']}", skipped)]

        self.c.exec(dcmds, title="setup-networks")

        l3admin = spec.get("l3admin")
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
            for link in spec.get("_links", []):
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

        if "cmds" in spec:
            self.c.exec(spec.get("cmds", []), title="cmds")

        if "ansible" in spec:
            self.c.ansible(spec["ansible"])
