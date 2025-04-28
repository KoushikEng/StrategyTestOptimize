from abc import ABC, abstractmethod

class Base(ABC):
    """Base class for strategies.
    """
    
    @abstractmethod
    def init(self):
        pass
    
    @abstractmethod
    def run(self):
        pass