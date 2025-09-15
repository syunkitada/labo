import json
import logging
from mylabo.lib.context import context


def init(ctx: context.Context):
    if ctx.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logger = logging.getLogger()
    logger.setLevel(log_level)

    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter())
    logger.addHandler(handler)


DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


class CustomFormatter(logging.Formatter):
    def format(self, record):
        message = {
            "time": self.formatTime(record, DATE_FORMAT),
            "level": record.levelname,
            "file": record.filename + ":" + str(record.lineno) + ":" + record.funcName,
            "msg": record.msg,
        }

        trace_id = None
        if "trace_id" in record.__dict__:
            trace_id = record.__dict__["trace_id"]
            message["trace_id"] = trace_id

        if "metadata" in record.__dict__:
            message["metadata"] = record.__dict__["metadata"]

        return json.dumps(message, separators=(",", ":"))
