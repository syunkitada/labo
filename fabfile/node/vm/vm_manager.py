import os

import time
import yaml


def make(nctx):
    if nctx.cmd == "dump":
        print(yaml.safe_dump(nctx.rspec))
    elif nctx.cmd == "make" or nctx.cmd == "remake":
        if nctx.cmd == "remake":
            _clean(nctx)

        if nctx.next == 0:
            _make_prepare(nctx)
            nctx.next = 1
        elif nctx.next == 1:
            _wait_for_active(nctx)
            nctx.next = 2
        elif nctx.next == 2:
            _make(nctx)
            nctx.next = -1
    elif nctx.cmd == "clean":
        _clean(nctx)
    elif nctx.cmd == "test":
        return _test(nctx)


def _clean(nctx):
    lcmds = [
        f"vm-ctl delete {nctx.rspec['_hostname']}",
    ]
    nctx.exec(lcmds, title="delete-vm", is_local=True)


def _test(nctx):
    pass


def _ping(nctx, target):
    pass


def _cmd(nctx, cmd):
    pass


def _make_prepare(nctx):
    spec = nctx.spec
    rspec = nctx.rspec
    os.makedirs(rspec["_script_dir"], exist_ok=True)
    nctx.c.sudo(f"rm -rf {rspec['_script_dir']}/*", hide=True)

    lcmds = [
        f"mkdir -p /mnt/nfs/vms/{nctx.rspec['_hostname']}",
    ]
    nctx.exec(lcmds, title="prepare-vm", is_local=True)

    links = []
    for link in rspec["_links"]:
        inets = []
        for peer_ip in link.get("peer_ips", []):
            inets.append(peer_ip['inet'])
        links.append({
            "name": link["link_name"],
            "inets": inets,
            "mac": link["peer_mac"],
        })

    vm_yaml = {
        "image": nctx.rspec["image"],
        "vcpus": nctx.rspec["vcpus"],
        "ram": nctx.rspec["ram"],
        "disk": nctx.rspec["disk"],
        "links": links,
        "routes": rspec.get("routes", []),
        "nfs": spec["common"]["nfs"],
        "resolvers": spec.get("common", {}).get("resolvers", []),
        "user": nctx.rspec["user"],
    }
    nctx.write(f"/mnt/nfs/vms/{nctx.rspec['_hostname']}/vm.yaml", yaml=vm_yaml, is_local=True)

    lcmds = [
        f"vm-ctl start {nctx.rspec['_hostname']}",
    ]
    nctx.exec(lcmds, title="prepare-vm", is_local=True)


def _wait_for_active(nctx):
    # vmに疎通が取れるまでまつ
    for i in range(1, 5):
        result = nctx.exec_without_log("ls", warn=True)
        if result.return_code == 0:
            break
        print(f"sleep {i * 2}")
        time.sleep(i * 2)


def _make(nctx):
    rspec = nctx.rspec

    if "cmds" in rspec:
        nctx.exec(rspec.get("cmds", []), title="cmds")

    if "ansible" in rspec:
        nctx.ansible(rspec['ansible'])
