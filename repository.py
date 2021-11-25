import abc
import model

class AbstractRepository(abc.ABC):

    @abc.abstractmethod
    def add(self, bach: model.Bach):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError