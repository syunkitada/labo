import fabric

from mylabo.lib import resource_controller
from mylabo.lib.utils import runtime, spec_utils


@fabric.task
def delete(c, file, debug=False, Dryrun=False):
    """apply [file] -d -D

    # target (default=node)
    コマンドの実行対象を限定するために使用します。
    kindは、infra, image, node のいずれかを指定でき、実行対象の種別を限定します。（デフォルトはnodeです）
    [kind]の後ろに、:[name_regex]を指定することで、正規表現により実行対象の名前で限定します。
    """

    specs = spec_utils.load_specs(file)
    for spec in specs:
        delete_spec(spec)


def delete_spec(spec):
    ctx = runtime.new(spec)

    rc = resource_controller.load(spec["kind"])
    rc.delete(ctx, spec)
