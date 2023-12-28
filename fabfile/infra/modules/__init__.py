from . import docker, mysql, nfs, pdns, shell


def make(t):
    # cmd, c, spec, rspec
    print(f"{t.cmd} infra {t.rspec['name']}: start")
    if t.rspec["kind"] == "docker":
        docker.cmd(t)
    elif t.rspec["kind"] == "mysql":
        mysql.cmd(t)
    elif t.rspec["kind"] == "pdns":
        pdns.cmd(t)
    elif t.rspec["kind"] == "nfs":
        nfs.cmd(t)
    elif t.rspec["kind"] == "shell":
        shell.cmd(t)
    else:
        print(f"unsupported kind: kind={t.rspec['kind']}")
        exit(1)
    print(f"{t.cmd} infra {t.rspec['name']}: completed")
