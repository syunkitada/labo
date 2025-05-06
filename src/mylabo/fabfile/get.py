import fabric

from mylabo.lib import resource_controller
from mylabo.lib.utils import runtime, spec_utils


@fabric.task
def get(c, kind, debug=False, Dryrun=False):
    """get [kind] -d -D

    # target (default=node)
    コマンドの実行対象を限定するために使用します。
    kindは、infra, image, node のいずれかを指定でき、実行対象の種別を限定します。（デフォルトはnodeです）
    [kind]の後ろに、:[name_regex]を指定することで、正規表現により実行対象の名前で限定します。
    """

    ctx = {}
    spec = {}

    rc = resource_controller.load(kind)
    rc.get(ctx, spec)
