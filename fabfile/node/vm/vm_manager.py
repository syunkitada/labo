import os

import yaml
from lib import colors


def make(nctx):
    if nctx.cmd == "dump":
        print(yaml.safe_dump(nctx.rspec))
    elif nctx.cmd == "make":
        if nctx.next == 0:
            _make_prepare(nctx)
            nctx.next = 1
        elif nctx.next == 1:
            _make(nctx)
            nctx.next = -1
    elif nctx.cmd == "remake":
        if nctx.next == 0:
            _clean(nctx)
            _make_prepare(nctx)
            nctx.next = 1
        elif nctx.next == 1:
            _make(nctx)
            nctx.next = -1
    elif nctx.cmd == "clean":
        _clean(nctx)
    elif nctx.cmd == "test":
        return _test(nctx)


def _clean(nctx):
    lcmds = [
        f"./tools/vm-ctl/main.py delete {nctx.rspec['_hostname']}",
    ]
    nctx.exec(lcmds, title="delete-vm", is_local=True)


def _test(nctx):
    pass


def _ping(nctx, target):
    pass


def _cmd(nctx, cmd):
    pass


def _make_prepare(nctx):
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
        # "nfs": {
        #     "target": "",
        #     "path": "",
        # },
    }
    nctx.write(f"/mnt/nfs/vms/{nctx.rspec['_hostname']}/vm.yaml", yaml=vm_yaml, is_local=True)

    lcmds = [
        f"./tools/vm-ctl/main.py start {nctx.rspec['_hostname']}",
    ]
    nctx.exec(lcmds, title="prepare-vm", is_local=True)


def _make(nctx):
    pass
