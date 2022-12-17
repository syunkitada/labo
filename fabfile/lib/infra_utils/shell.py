# nfs utils


def cmd(cmd, c, spec, rspec):
    if cmd == "dump":
        print(rspec)
    elif cmd == "make":
        _make(c, spec, rspec)


def _make(c, spec, rspec):
    for cmd in rspec["cmds"]:
        c.sudo(cmd)
