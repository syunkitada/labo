import fabric

from mylabo.lib import resource_controller
from mylabo.lib.logger import logger
from mylabo.lib.utils import spec_utils, cmd_utils
import yaml


@fabric.task
def debug(c, file="", debug=False, Dryrun=False, label=""):
    """debug [file] -d -D

    # target (default=node)
    コマンドの実行対象を限定するために使用します。
    kindは、infra, image, node のいずれかを指定でき、実行対象の種別を限定します。（デフォルトはnodeです）
    [kind]の後ろに、:[name_regex]を指定することで、正規表現により実行対象の名前で限定します。
    """

    logger.init(debug)

    specs = spec_utils.load_specs(file)
    for spec in specs:
        yaml_str = yaml.dump(spec, allow_unicode=True)
        print(yaml_str)
