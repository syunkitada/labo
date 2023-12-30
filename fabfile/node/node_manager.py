import traceback

from fabric import Connection
from lib import colors
from node.container import container_manager
from node.vm import vm_manager


def make(nctx):
    print(f"{nctx.cmd} node {nctx.rspec['name']}: start {nctx.next}")
    result = None
    try:
        if nctx.rspec["kind"] == "container":
            container_manager.make(nctx)
        elif nctx.rspec["kind"] == "vm":
            vm_manager.make(nctx)
        # result = nctx.cmd()
        # if t.rspec["kind"] == "gw":
        #     result = router.cmd(t.cmd, t.c, t.spec, t.rspec)
        # if nctx.rspec["kind"] == "container":
        #     if nctx.rc is None:
        #         nctx.rc = container_context.Context(nctx)
        #     result = container.cmd(nctx)
        # elif t.rspec["kind"] == "vm":
        #     result = vm.cmd(t.cmd, t.c, t.spec, t.rspec)
        # else:
        #     print(f"unsupported kind: kind={t.rspec['kind']}")
        #     exit(1)
    except Exception as e:
        result = {"status": 1, "msg": colors.crit(f"{str(e)}\n{traceback.format_exc()}")}
        nctx.next = -1

    if nctx.next > 0:
        print(f"{nctx.cmd} node {nctx.rspec['name']}: next {nctx.next}")
    else:
        print(f"{nctx.cmd} node {nctx.rspec['name']}: completed")

        # fabricのConnectionの場合は、使い終わったら閉じる
        if type(nctx.c) is Connection:
            nctx.c.close()

    return {
        "name": nctx.rspec["name"],
        "result": result,
    }
