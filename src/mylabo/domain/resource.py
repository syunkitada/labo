from abc import ABC, abstractmethod


class Resource(ABC):
    @abstractmethod
    def get(self, labels: dict):
        pass

    @abstractmethod
    def apply(self, labels: dict):
        pass

    @abstractmethod
    def delete(self, labels: dict):
        pass
