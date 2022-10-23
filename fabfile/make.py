import getpass
import yaml
from fabric import task, Config, Connection

from lib.virt_utils import router, vm
from lib.nfs_utils import nfs


@task
def make(_, file, target="all", host="localhost"):
    with open(file) as f:
        env_file = yaml.safe_load(f)

    sudo_pass = getpass.getpass("Input your sudo password > ")
    config = Config()
    config["sudo"] = {"password": sudo_pass}

    conn = Connection(host, config=config)

    make_infra = False
    make_node = False
    if target == "all" or target == "infra":
        make_infra = True
    if target == "all" or target == "node":
        make_node = True

    infra_map = {}
    for node in env_file["infra"]:
        infra_map[node["name"]] = node
        if not make_infra:
            continue
        if node["kind"] == "nfs":
            nfs.make_nfs(conn, node)
        elif node["kind"] == "gw":
            router.make_gw(conn, node)

        if not make_infra:
            continue

    if make_infra:
        for name, image in env_file["vm_image"].items():
            image["name"] = name
            vm.make_image(conn, image, infra_map)

    if make_node:
        for node in env_file["node"]:
            if node["kind"] == "vm":
                vm.make_vm(conn, node)
