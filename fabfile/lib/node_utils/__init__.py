from fabric import Connection

from . import container_context, router, container, vm, vm_image


def make(t):
    print(f"{t.cmd} node {t.rspec['name']}: start {t.next}")
    result = None
    if t.rspec["kind"] == "gw":
        result = router.cmd(t.cmd, t.c, t.spec, t.rspec)
    elif t.rspec["kind"] == "container":
        if t.ctx is None:
            t.ctx = container_context.Context(t)
        result = container.cmd(t)
    elif t.rspec["kind"] == "vm":
        result = vm.cmd(t.cmd, t.c, t.spec, t.rspec)
    else:
        print(f"unsupported kind: kind={t.rspec['kind']}")
        exit(1)

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
