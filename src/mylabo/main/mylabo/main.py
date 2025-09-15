#!/usr/bin/env python3

import os
import re
import sys


def main():
    sys.argv[0] = re.sub(r"(-script\.pyw|\.exe)?$", "", sys.argv[0])

    root_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    root_path = os.path.abspath(root_path)

    sys.argv = [sys.argv[0], "-r", root_path] + sys.argv[1:]

    from fabric import Config, Executor
    from fabric import __version__ as fabric
    from fabric.main import Fab

    fab = Fab(
        name="Fabric",
        version=fabric,
        executor_class=Executor,
        config_class=Config,
    )

    sys.exit(fab.run())
