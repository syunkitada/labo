import fabric

from mylabo.lib import resource_controller
from mylabo.lib.logger import logger
from mylabo.lib.utils import spec_utils, cmd_utils


@fabric.task
def test(c, file="", debug=False, Dryrun=False, label=""):
    """test [kind] [name] -d -D

    # target (default=node)
    コマンドの実行対象を限定するために使用します。
    kindは、infra, image, node のいずれかを指定でき、実行対象の種別を限定します。（デフォルトはnodeです）
    [kind]の後ろに、:[name_regex]を指定することで、正規表現により実行対象の名前で限定します。
    """

    labels = cmd_utils.parse_labels(label)
    logger.init(debug)

    specs = spec_utils.load_specs(file)
    for spec in specs:
        test_spec(spec, labels)


def test_spec(spec, labels: dict):
    rc = resource_controller.load(spec)
    rc.test(labels)
