from abc import ABC, abstractmethod


class ExecuteGroverSearch(ABC):
    @abstractmethod
    def grover_oracle(self): ...

    @abstractmethod
    def grover_diffusion(self): ...

    @abstractmethod
    def grover_circuit(self): ...

    @abstractmethod
    def run(self): ...
