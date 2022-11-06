import re
import os
from fabric import task, Config, Connection

from lib.virt_utils import router, container, vm, vm_image
from lib.nfs_utils import nfs
from lib.ctx_utils import patch_ctx
from lib.resolver_utils import pdns
from lib.mysql_utils import mysql
from lib.spec_utils import loader
from lib import bootstrap_utils


@task
def make(c, file, target="all", cmd="make"):
    spec = loader.load_spec(file)

    context_config = {}
    context_config.update(
        {
            "run": {
                "echo": True,
                "echo_format": "{command}",
            },
            "sudo": {
                "echo": True,
                "echo_format": "{command}",
            },
            "local": {
                "echo": True,
                "echo_format": "{command}",
            },
        }
    )
    if os.environ.get("SUDO_USER") is None:
        print("Use sudo")
        exit(1)

    common = spec.get("common")
    host = None
    connect_kwargs = {}
    if common is not None:
        host_pass = common.get("host_pass")
        if host_pass is not None:
            context_config["sudo"]["password"] = host_pass
            connect_kwargs["password"] = host_pass
        host_user = common.get("host_user")
        if host_user is not None:
            context_config["user"] = host_user
        host = common.get("host")
    if host is not None:
        c = Connection(host, config=Config(context_config), connect_kwargs=connect_kwargs)
    else:
        c.config.update(context_config)

    if cmd == "bootstrap":
        bootstrap_utils.init(c, spec)

    patch_ctx(c)
    c.update_ctx()

    re_targets = []
    targets = target.split(":")
    target_kind = targets[0]
    if len(targets) > 1:
        target_strs = targets[1].split(",")
        for t in target_strs:
            re_targets.append(re.compile(t))

    make_infra = False
    make_image = False
    make_node = False
    if target_kind == "all" or target_kind == "infra":
        make_infra = True
    if target_kind == "all" or target_kind == "node":
        make_node = True
    if target_kind == "image":
        make_image = True

    is_make = False
    if cmd == "make":
        is_make = True

    if make_infra:
        for rspec in spec.get("infras", []):
            if not_target(rspec, re_targets):
                continue
            elif rspec["kind"] == "mysql":
                if is_make:
                    mysql.make(c, spec, rspec)
            elif rspec["kind"] == "pdns":
                if is_make:
                    pdns.make(c, spec, rspec)
            elif rspec["kind"] == "nfs":
                if is_make:
                    nfs.make(c, spec, rspec)

    if make_image:
        for rspec in spec.get("vm_images", []):
            if not_target(rspec, re_targets):
                continue
            vm_image.cmd(cmd, c, spec, rspec)

    if make_node:
        for rspec in spec.get("nodes", []):
            if not_target(rspec, re_targets):
                continue
            elif rspec["kind"] == "gw":
                if is_make:
                    router.make_gw(c, spec, rspec)
            elif rspec["kind"] == "container":
                if is_make:
                    container.make(c, spec, rspec)
            elif rspec["kind"] == "vm":
                vm.cmd(cmd, c, spec, rspec)


def not_target(rspec, re_targets):
    if len(re_targets) == 0:
        return False
    name = rspec["name"]
    for r in re_targets:
        if r.match(name):
            return False
    return True
