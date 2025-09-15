import fabric

from mylabo import resource_controller
from mylabo.lib.logger import logger
from mylabo.lib.manifest import manifest_loader
from mylabo.lib.context import context


@fabric.task
def test(c, file="", debug=False, Dryrun=False, labels=""):
    """test -f [file] -d -D -l [labels]

    # labels
    -l name=value,name!=value,...
    """

    ctx = context.Context(invoke_ctx=c, debug=debug, dryrun=Dryrun, labels=labels)
    logger.init(ctx)

    manifests = manifest_loader.load_manifests(file)
    for manifest in manifests:
        test_manifest(ctx, manifest)


def test_manifest(ctx: context.Context, manifest: dict):
    rc = resource_controller.load(ctx, manifest)
    rc.test()
