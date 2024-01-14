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
            result = container_manager.make(nctx)
        elif nctx.rspec["kind"] == "vm":
            result = vm_manager.make(nctx)
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
