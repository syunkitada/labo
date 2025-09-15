import fabric

from mylabo import resource_controller
from mylabo.lib.logger import logger
from mylabo.lib.manifest import manifest_loader
from mylabo.lib.context import context


@fabric.task
def delete(c, file, debug=False, Dryrun=False, labels=""):
    """delete -f [file] -d -D -l [labels]

    # labels
    -l name=value,name!=value,...
    """

    ctx = context.Context(invoke_ctx=c, debug=debug, dryrun=Dryrun, labels=labels)
    logger.init(ctx)

    manifests = manifest_loader.load_manifests(file)
    for manifest in manifests:
        delete_manifest(ctx, manifest)


def delete_manifest(ctx: context.Context, manifest: dict):
    rc = resource_controller.load(ctx, manifest)
    rc.delete()
