import re
import os
import yaml
from invoke.context import Context
from fabric import task, Config, Connection
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict

from lib import colors, spec_utils, os_utils, infra_utils, node_utils


@task
def make(c, file, target="node", cmd="make", debug=False, Dryrun=False, parallel_pool_size=5):
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
    os.makedirs(spec["_script_dir"], exist_ok=True)
    completed_spec_file = os.path.join(spec["_script_dir"], "spec.yaml")
    with open(completed_spec_file, "w") as f:
        f.write(yaml.safe_dump(spec))
    print(f"completed spec was saved to {completed_spec_file}")

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

    infra_utils.envrc.cmd(Task(context_config=context_config, cmd=cmd, spec=spec, rspec=None, debug=debug, dryrun=Dryrun))

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
            if _not_target(rspec, re_targets):
                print(f"{cmd} infra {rspec['name']}: skipped")
                continue
            infra_utils.make(Task(context_config=context_config, cmd=cmd, spec=spec, rspec=rspec, debug=debug, dryrun=Dryrun))

    if make_image:
        for name, rspec in spec.get("vm_image_map", {}).items():
            if _not_target(rspec, re_targets):
                print(f"{cmd} image {name}: skipped")
                continue
            node_utils.make_vm_image(Task(context_config=context_config, cmd=cmd, spec=spec, rspec=rspec, debug=debug, dryrun=Dryrun))

    if make_node:
        ctx_data = {
            "netns_map": os_utils.get_netns_map(c),
            "docker_ps_map": infra_utils.docker.get_docker_ps_map(c),
        }

        results = OrderedDict()
        tasks = []
        for rspec in spec.get("nodes", []):
            if _not_target(rspec, re_targets):
                print(f"{cmd} node {rspec['name']}: skipped")
                continue
            tasks.append(
                Task(context_config=context_config, cmd=cmd, spec=spec, rspec=rspec, debug=debug, dryrun=Dryrun, ctx_data=ctx_data)
            )
            results[rspec["name"]] = []

        while True:
            with ThreadPoolExecutor(max_workers=parallel_pool_size) as pool:
                tmp_results = pool.map(node_utils.make, tasks)
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

        _print_results(results)
        _dump_scripts(spec, cmd, tasks)

        return


def _print_results(results):
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


def _dump_scripts(spec, cmd, tasks):
    script_path = os.path.join(spec["_script_dir"], f"{cmd}.sh")
    separator = "#" + "-" * 100
    cmds = []
    for t in tasks:
        if t.rc is None:
            continue
        cmds += [
            separator,
            f"# {t.rspec['name']} start",
            separator,
        ]
        cmds += t.rc.full_cmds
        cmds += [
            separator,
            f"# {t.rspec['name']} end",
            separator,
            "",
        ]

    with open(script_path, "w") as f:
        f.write("\n".join(cmds))


class Task:
    def __init__(self, context_config, spec, cmd, rspec, debug, dryrun, ctx_data={}):
        self.c = _new_runtime_context(context_config, spec)
        self.cmd = cmd
        self.spec = spec
        self.rspec = rspec
        self.ctx_data = ctx_data
        self.next = 0
        self.debug = debug
        self.dryrun = dryrun
        self.rc = None


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


def _not_target(rspec, re_targets):
    if len(re_targets) == 0:
        return False
    name = rspec["name"]
    for r in re_targets:
        if r.match(name):
            return False
    return True
