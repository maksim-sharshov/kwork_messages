from abc import ABC, abstractmethod
from core.logger import logger


class BaseManager(ABC):
    timeout: int = 60

    def __init__(self):
        self.logger = logger

    @abstractmethod
    async def task(self):
        pass

    @abstractmethod
    async def run(self):
        pass