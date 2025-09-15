from typing import Any
from pydantic import BaseModel
from invoke import context


class Context(BaseModel):
    invoke_ctx: Any
    debug: bool
    dryrun: bool
    labels: dict[str, str]

    def __init__(self, invoke_ctx: context.Context = None, debug=False, dryrun=False, labels=""):
        labels_dict = {}

        if labels is not None and labels != "":
            labels_strs = labels.split(",")
            for labels_str in labels_strs:
                key_value = labels_str.split("=")
                if len(key_value) != 2:
                    raise ValueError(f"Invalid label format: {labels_str}. Expected format is key=value.")
                labels_dict[key_value[0]] = key_value[1]

        super().__init__(invoke_ctx=invoke_ctx, debug=debug, dryrun=dryrun, labels=labels_dict)
