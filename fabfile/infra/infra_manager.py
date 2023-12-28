from .modules import docker, mysql, nfs, pdns, shell


def make(nctx):
    # cmd, c, spec, rspec
    print(f"{nctx.cmd} infra {nctx.rspec['name']}: start")
    if nctx.rspec["kind"] == "docker":
        docker.cmd(nctx)
    elif nctx.rspec["kind"] == "mysql":
        mysql.cmd(nctx)
    elif nctx.rspec["kind"] == "pdns":
        pdns.cmd(nctx)
    elif nctx.rspec["kind"] == "nfs":
        nfs.cmd(nctx)
    elif nctx.rspec["kind"] == "shell":
        shell.cmd(nctx)
    else:
        print(f"unsupported kind: kind={nctx.rspec['kind']}")
        exit(1)
    print(f"{nctx.cmd} infra {nctx.rspec['name']}: completed")
