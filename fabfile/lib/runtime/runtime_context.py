import os
from invoke import context as invoke
import fabric


def new(spec):
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

    return _new_runtime_context(context_config, spec)

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
        c = fabric.Connection(host, config=fabric.Config(context_config), connect_kwargs=connect_kwargs)
        c.is_local = False
    else:
        c = invoke.Context(config=invoke.Config(context_config))
        c.is_local = True

    return c
