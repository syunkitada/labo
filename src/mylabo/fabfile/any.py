import fabric

from mylabo import resource_controller
from mylabo.domain import resource
from mylabo.lib.logger import logger
from mylabo.lib.manifest import manifest_loader
from mylabo.lib.context import context
from mylabo.lib.utils import cmd_utils


@fabric.task
def any(c, file="", debug=False, Dryrun=False, labels="", action=""):
    """any -f [file] -d -D -l [labels], -a [action]

    # labels
    -l name=value,name!=value,...
    """

    ctx = context.Context(invoke_ctx=c, debug=debug, dryrun=Dryrun, labels=labels)
    logger.init(ctx)

    action = cmd_utils.parse_action(action)

    manifests = manifest_loader.load_manifests(file)
    for manifest in manifests:
        any_manifest(ctx, manifest, action)


def any_manifest(ctx: context.Context, manifest: dict, action: resource.AnyAction):
    rc = resource_controller.load(ctx, manifest)
    results = rc.any(action)
    for result in results:
        if isinstance(result, dict):
            print(
                f"{result.get('name', 'unknown')}: {result.get('id', 'id:unknown')}: {result.get('status', 'unknown')}"
            )
        else:
            print(result)
