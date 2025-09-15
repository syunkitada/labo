import fabric

# from mylabo import resource_controller
from mylabo.lib.logger import logger
from mylabo.lib.manifest import manifest_loader
import yaml
from mylabo.lib.context import context


@fabric.task
def debug(c, file="", debug=False, Dryrun=False, labels=""):
    """debug -f [file] -d -D -l [labels]

    # labels
    -l name=value,name!=value,...
    """

    ctx = context.Context(invoke_ctx=c, debug=debug, dryrun=Dryrun, labels=labels)
    logger.init(ctx)

    manifests = manifest_loader.load_manifests(file)
    for manifest in manifests:
        yaml_str = yaml.dump(manifest, allow_unicode=True)
        print(yaml_str)
