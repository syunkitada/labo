# nfs utils


def cmd(t):
    if t.cmd == "dump":
        print(t.rspec)
    elif cmd == "make":
        _make(t)


def _make(t):
    for cmd in t.rspec["cmds"]:
        t.c.sudo(cmd)
