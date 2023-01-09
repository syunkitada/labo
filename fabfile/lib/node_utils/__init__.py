import traceback
from fabric import Connection

from lib import colors
from . import container_context, router, container, vm, vm_image


def make(t):
    print(f"{t.cmd} node {t.rspec['name']}: start {t.next}")
    result = None
    try:
        if t.rspec["kind"] == "gw":
            result = router.cmd(t.cmd, t.c, t.spec, t.rspec)
        elif t.rspec["kind"] == "container":
            if t.rc is None:
                t.rc = container_context.Context(t)
            result = container.cmd(t)
        elif t.rspec["kind"] == "vm":
            result = vm.cmd(t.cmd, t.c, t.spec, t.rspec)
        else:
            print(f"unsupported kind: kind={t.rspec['kind']}")
            exit(1)
    except Exception as e:
        result = {"status": 1, "msg": colors.crit(f"{str(e)}\n{traceback.format_exc()}")}
        t.next = -1

    if t.next > 0:
        print(f"{t.cmd} node {t.rspec['name']}: next {t.next}")
    else:
        print(f"{t.cmd} node {t.rspec['name']}: completed")

        # fabricのConnectionの場合は、使い終わったら閉じる
        if type(t.c) is Connection:
            t.c.close()

    return {
        "name": t.rspec["name"],
        "result": result,
    }


def make_vm_image(t):
    print(f"{t.cmd} image {t.rspec['name']}: start")
    vm_image.cmd(t)
    print(f"{t.cmd} image {t.rspec['name']}: completed")
