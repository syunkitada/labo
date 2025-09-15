from abc import ABC, abstractmethod
from pydantic import BaseModel
from mylabo.lib.context import context


class AnyAction(BaseModel):
    action: str
    kwargs: dict[str, str]

    def __init__(self, action: str):
        if action is None or action == "":
            return {}

        label_strs = action.split(",")
        action = label_strs.pop(0)

        kwargs = {}
        for label_str in label_strs:
            key_value = label_str.split("=")
            if len(key_value) != 2:
                raise ValueError(f"Invalid action format: {label_str}. Expected format is key=value.")
            kwargs[key_value[0]] = key_value[1]

        super().__init__(action=action, kwargs=kwargs)


class Resource(ABC):
    @abstractmethod
    def __init__(self, ctx: context.Context, manifest: dict):
        pass

    @abstractmethod
    def get(self):
        pass

    @abstractmethod
    def apply(self):
        pass

    @abstractmethod
    def delete(self):
        pass

    @abstractmethod
    def test(self):
        pass

    @abstractmethod
    def any(self, action: AnyAction):
        pass
