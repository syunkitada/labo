"""
envrc は、環境変数を扱うためのリソースです。
"""


def cmd(t):
    if t.cmd == "make":
        make(t.c, t.spec)


def make(c, spec):
    envs = []
    for key, value in spec.get("_env_map", {}).items():
        envs.append(f"export {key}={value}")
    envs_str = "\n".join(envs)
    c.run(f"cat << EOS > /tmp/.laboenvrc\n{envs_str}\nEOS", hide=True)

    if not c.is_local:
        c.put("/tmp/.laboenvrc", "/tmp/.laboenvrc")
