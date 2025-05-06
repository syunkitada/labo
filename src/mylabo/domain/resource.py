from abc import ABC, abstractmethod


class Resource(ABC):
    @abstractmethod
    def get(self, ctx, spec):
        pass

    @abstractmethod
    def apply(self, ctx, spec):
        pass

    @abstractmethod
    def delete(self, ctx, spec):
        pass
