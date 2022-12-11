import yaml
import time
import os


def cmd(cmd, c, spec, rspec):
    if cmd == "dump":
        print(yaml.safe_dump(rspec))
    elif cmd == "make":
        _make(c, spec, rspec)
    elif cmd == "clean":
        _clean(c, spec, rspec)


def _clean(c, spec, rspec):
    if rspec["_hostname"] in c.docker_ps_map:
        c.sudo(f"docker kill {rspec['_hostname']}")
    if rspec["_hostname"] in c.netns_map:
        c.sudo(f"rm -rf /var/run/netns/{rspec['_hostname']}")


def _exec(c, rspec, cmds, title="", dryrun=False, netns=False, docker=False):
    exec_filepath = os.path.join(rspec["_script_dir"], f"{rspec['_script_index']}_{title}_exec.sh")
    full_filepath = os.path.join(rspec["_script_dir"], f"{rspec['_script_index']}_{title}_full.sh")
    rspec["_script_index"] += 1

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
        if docker:
            cmds_str = "\n".join(exec_cmds)
            f.write(f"docker exec {rspec['_hostname']} bash -ex -c '\n{cmds_str}'\n")
        elif netns:
            cmds_str = "\n".join(exec_cmds)
            f.write(f"ip netns exec {rspec['_hostname']} bash -ex -c '\n{cmds_str}'\n")
        else:
            f.write("\n".join(exec_cmds))
    if len(exec_cmds) > 0:
        c.sudo(f"bash -ex {exec_filepath}")

    with open(full_filepath, "w") as f:
        if docker:
            cmds_str = "\n".join(full_cmds)
            f.write(f"docker exec {rspec['_hostname']} bash -ex -c '\n{cmds_str}\n'\n")
        elif netns:
            cmds_str = "\n".join(full_cmds)
            f.write(f"ip netns exec {rspec['_hostname']} bash -ex -c '\n{cmds_str}\n'\n")
        else:
            f.write("\n".join(full_cmds))

    cmds.clear()


def _netns_ip_addr_add(c, cmds, rspec, ip, dev):
    if ip["version"] == 4:
        dryrun = True
        if (
            rspec["_hostname"] not in c.netns_map
            or dev not in c.netns_map[rspec["_hostname"]]["netdev_map"]
            or ip["inet"] not in c.netns_map[rspec["_hostname"]]["netdev_map"][dev]["inet_map"]
        ):
            dryrun = False
        cmds += [(f"ip addr add {ip['inet']} dev {dev}", dryrun)]
    elif ip["version"] == 6:
        dryrun = True
        if (
            rspec["_hostname"] not in c.netns_map
            or dev not in c.netns_map[rspec["_hostname"]]["netdev_map"]
            or ip["inet"] not in c.netns_map[rspec["_hostname"]]["netdev_map"][dev]["inet6_map"]
        ):
            dryrun = False
        cmds += [(f"ip addr add {ip['inet']} dev {dev}", dryrun)]


def _link(c, cmds, rspec, link, is_peer=False):
    dryrun = True
    if not is_peer:
        if rspec["_hostname"] not in c.netns_map or link["link_name"] not in c.netns_map[rspec["_hostname"]]["netdev_map"]:
            dryrun = False
        cmds += [
            (f"ip link add {link['link_name']} type veth peer name {link['peer_name']}", dryrun),
            (f"ethtool -K {link['link_name']} tso off tx off", dryrun),
            (f"ethtool -K {link['peer_name']} tso off tx off", dryrun),
            (f"ip link set dev {link['link_name']} mtu {link['mtu']}", dryrun),
            (f"ip link set dev {link['link_name']} netns {rspec['_hostname']} up", dryrun),
        ]
    else:
        if rspec["_hostname"] not in c.netns_map or link["peer_name"] not in c.netns_map[rspec["_hostname"]]["netdev_map"]:
            dryrun = False
        cmds += [
            (f"ip link set dev {link['peer_name']} mtu {link['mtu']}", dryrun),
            (f"ip link set dev {link['peer_name']} netns {rspec['_hostname']} up", dryrun),
        ]


def _make(c, spec, rspec):
    os.makedirs(rspec["_script_dir"], exist_ok=True)
    c.sudo(f"rm -rf {rspec['_script_dir']}/*", hide=True)

    dryrun = True
    cmds = [
        f"docker run -d -it --privileged --rm --network none -v {rspec['_script_dir']}:{rspec['_script_dir']} --name {rspec['_hostname']} {rspec['image']}",
        f"pid=`docker inspect {rspec['_hostname']}" + " --format '{{.State.Pid}}'`",
        "ln -sfT /proc/${pid}/ns/net " + f"/var/run/netns/{rspec['_hostname']}",
    ]
    if rspec["_hostname"] not in c.docker_ps_map:
        dryrun = False
    _exec(c, rspec, cmds, title="prepare-docker", dryrun=dryrun)

    for key, value in rspec.get("sysctl_map", {}).items():
        cmds += [f"sysctl -w {key}={value}"]
    _exec(c, rspec, cmds, title="docker-sysctl", docker=True)

    netns_cmds = []
    for ip in rspec.get("lo_ips", []):
        _netns_ip_addr_add(c, netns_cmds, rspec, ip, "lo")

    for link in rspec.get("links", []):
        _link(c, cmds, rspec, link)

        for ip in link.get("ips", []):
            _netns_ip_addr_add(c, netns_cmds, rspec, ip, link["link_name"])

    for link in rspec.get("_links", []):
        _link(c, cmds, rspec, link, is_peer=True)

    _exec(c, rspec, cmds, title="prepare-links")
    _exec(c, rspec, netns_cmds, title="prepare-netns", netns=True)

    # for route in node.get("routes", []):
    #     if route["dst"] not in netns["route_map"]:
    #         c.sudo("ip route add {route['dst']} via {route['via']}")

    print("script_dir", rspec["_script_dir"])
