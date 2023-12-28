import os
import re
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

import yaml
from invoke import context as invoke
import fabric
from lib import colors, node_utils, os_utils, spec_utils, task_utils
from lib.runtime import runtime_context
from infra import infra_context, infra_manager
from node import node_context
from tabulate import tabulate


@fabric.task
def make_infra(c, file, target="", cmd="make", debug=False, Dryrun=False, parallel_pool_size=5):
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

    # Dryrun (default=False)
    Dryrunモードで実行します。

    # parallel_pool_size (default=5)
    並列実行のプールサイズです。
    """

    spec = spec_utils.load_spec(file)
    cmds = cmd.split(":")

    c = runtime_context.new(spec)

    re_targets = task_utils.target.get_re_targets(target)

    for rspec in spec.get("infras", []):
        if not task_utils.target.is_target(rspec, re_targets):
            continue
        nctx = node_context.NodeContext(cmd=cmd, spec=spec, rspec=rspec, debug=debug, dryrun=Dryrun)
        infra_manager.make(nctx)
