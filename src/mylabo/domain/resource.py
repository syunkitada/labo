from abc import ABC, abstractmethod


class Resource(ABC):
    @abstractmethod
    def get(self):
        pass

    @abstractmethod
    def apply(self):
        pass

    @abstractmethod
    def delete(self):
        pass
