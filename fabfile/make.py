import re
import os
import yaml
from invoke.context import Context
from fabric import task, Config, Connection
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict

from lib.virt_utils import context, router, container, vm, vm_image
from lib.infra_utils import docker, mysql, pdns, nfs, envrc, shell
from lib import spec_utils, os_utils, colors


@task
def make(c, file, target="node", cmd="make", debug=False, parallel_pool_size=5):
    """make -f [spec_file] -t [kind]:[name_regex] -c [cmd] (-p [parallel_pool_size])

    # target (default=node)
    コマンドの実行対象を限定するために使用します。
    kindは、infra, image, node のいずれかを指定でき、実行対象の種別を限定します。（デフォルトはnodeです）
    [kind]の後ろに、:[name_regex]を指定することで、正規表現により実行対象の名前で限定します。

    # cmd (default=make)
    実行対象のリソースに対するコマンドを指定するために使用します。
    cmdは、make, dump などが指定でき、これはリソースによってサポートされるコマンドが異なります。（デフォルトはmakeです）
    makeは、リソースのスペックに基づいてリソースを実体化するコマンドで、すべてのリソースでサポートされています。

    # debug (default=False)
    実行ログを詳細化します。

    # parallel_pool_size (default=5)
    並列実行のプールサイズです。
    """

    spec = spec_utils.load_spec(file)
    if cmd == "dump-spec":
        print(yaml.safe_dump(spec))
        return

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

    c = _new_runtime_context(context_config, spec)
    envrc.cmd(cmd, c, spec)

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

    if make_infra:
        for rspec in spec.get("infras", []):
            print(f"{cmd} infra {rspec['name']}: start")
            if _not_target(rspec, re_targets):
                print(f"{cmd} infra {rspec['name']}: skipped")
                continue
            elif rspec["kind"] == "docker":
                docker.cmd(cmd, c, spec, rspec)
            elif rspec["kind"] == "mysql":
                mysql.cmd(cmd, c, spec, rspec)
            elif rspec["kind"] == "pdns":
                pdns.cmd(cmd, c, spec, rspec)
            elif rspec["kind"] == "nfs":
                nfs.cmd(cmd, c, spec, rspec)
            elif rspec["kind"] == "shell":
                shell.cmd(cmd, c, spec, rspec)
            else:
                print(f"unsupported kind: kind={rspec['kind']}")
                exit(1)
            print(f"{cmd} infra {rspec['name']}: completed")

    if make_image:
        for name, rspec in spec.get("vm_image_map", {}).items():
            print(f"{cmd} image {name}: start")
            if _not_target(rspec, re_targets):
                print(f"{cmd} image {name}: skipped")
                continue
            vm_image.cmd(cmd, c, spec, rspec)
            print(f"{cmd} image {name}: completed")

    if make_node:
        ctx_data = {
            "netns_map": os_utils.get_netns_map(c),
            "docker_ps_map": docker.get_docker_ps_map(c),
        }

        results = OrderedDict()
        tasks = []
        for rspec in spec.get("nodes", []):
            if _not_target(rspec, re_targets):
                print(f"{cmd} node {rspec['name']}: skipped")
                continue
            tasks.append(Task(context_config=context_config, cmd=cmd, spec=spec, rspec=rspec, ctx_data=ctx_data, debug=debug))
            results[rspec["name"]] = []

        while True:
            with ThreadPoolExecutor(max_workers=parallel_pool_size) as pool:
                tmp_results = pool.map(_make, tasks)
            for result in tmp_results:
                results[result["name"]].append(result["result"])

            next_tasks = []
            for t in tasks:
                # nextがインクリメントされた場合はそのタスクを継続します
                if t.next > 0:
                    next_tasks.append(t)
            if len(next_tasks) == 0:
                break
            tasks = next_tasks

        print("# results ----------------------------------------")
        msgs = []
        for name, results in results.items():
            last_result = results[-1]
            last_status = 0
            if last_result is None:
                msgs.append(colors.ok(f"{name}: success"))
            else:
                last_status = last_result.get("status", 0)
                if last_status == 0:
                    msgs.append(colors.ok(f"{name}: success"))
                else:
                    msgs.append(colors.crit(f"{name}: failed"))

            for result in results:
                if result is not None:
                    msgs.append(result.get("msg", ""))
        msg = "\n".join(msgs)
        print(msg)

        return


class Task:
    def __init__(self, context_config, ctx_data, spec, cmd, rspec, debug):
        self.c = _new_runtime_context(context_config, spec)
        self.cmd = cmd
        self.spec = spec
        self.rspec = rspec
        self.ctx_data = ctx_data
        self.next = 0
        self.ctx = None
        self.debug = debug


def _new_runtime_context(context_config, spec):
    """
    new_runtime_contextは、ローカルでの実行の場合はinvokeのContextを返し、リモートでの実行の場合はfabricのConnectionを返します。
    fabricはinvokeを利用されて実装されているので、ある程度の互換性を持っており、どちらを利用してるかを意識せずに実装できます。
    """
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
        c.is_local = False
    else:
        c = Context(config=context_config)
        c.is_local = True

    return c


def _make(t):
    print(f"{t.cmd} node {t.rspec['name']}: start {t.next}")
    result = None
    if t.rspec["kind"] == "gw":
        result = router.cmd(t.cmd, t.c, t.spec, t.rspec)
    elif t.rspec["kind"] == "container":
        if t.ctx is None:
            t.ctx = context.ContainerContext(t)
        result = container.cmd(t)
    elif t.rspec["kind"] == "vm":
        result = vm.cmd(t.cmd, t.c, t.spec, t.rspec)
    else:
        print(f"unsupported kind: kind={t.rspec['kind']}")
        exit(1)

    if t.next > 0:
        print(f"{t.cmd} node {t.rspec['name']}: next {t.next}")
    else:
        print(f"{t.cmd} node {t.rspec['name']}: completed")

        # fabricのConnectionの場合は、使い終わったら閉じる
        if type(t.c) is Connection:
            t.c.close()

    return {
        "name": t.rspec["name"],
        "result": result,
    }


def _not_target(rspec, re_targets):
    if len(re_targets) == 0:
        return False
    name = rspec["name"]
    for r in re_targets:
        if r.match(name):
            return False
    return True
