import numpy as np
from entities import GroverConfig
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from use_cases import ExecuteGroverSearch


class QiskitGroverSearch(ExecuteGroverSearch):
    def __init__(self, config: GroverConfig):
        super().__init__()
        self.config: GroverConfig = config
        self.n_qubits: int = len(config.marked_state)
        self.qc = QuantumCircuit(
            self.n_qubits + 1, self.n_qubits
        )  # extra one Ancilla for Oracle qubit
        self.iterations = (
            config.iteration
            if config.iteration
            else int(np.floor(np.pi / 4 * np.sqrt(2**self.n_qubits)))
        )

    def _apply_X_gate_to_zero_bits(self, bitstring: str) -> None:
        for qubit_index, bit in enumerate(reversed(bitstring)):
            if bit == "0":
                self.qc.x(qubit_index)
        self.qc.barrier()

    def grover_oracle(self) -> None:
        """
        Constructs Grover's Oracle.
        """
        self._apply_X_gate_to_zero_bits(self.config.marked_state)
        self.qc.mcx(
            list(range(self.n_qubits)), self.n_qubits
        )  # Ancilla (n+1) as target
        self._apply_X_gate_to_zero_bits(self.config.marked_state)

    def _apply_core_grover_diffusion(self) -> None:
        """
        Apply the core diffusion operator D_0 = 2|0><0| - I
        using multi-controlled gates.
        """
        self.qc.x(range(self.n_qubits))
        self.qc.h(self.n_qubits - 1)
        self.qc.barrier()

        # (n-1)-controlled
        self.qc.mcx(list(range(self.n_qubits - 1)), self.n_qubits - 1)

        self.qc.h(self.n_qubits - 1)
        self.qc.barrier()
        self.qc.x(range(self.n_qubits))

    def grover_diffusion(self) -> None:
        """
        Constructed Up to -1 Global Phase
        Apply Grover Diffusion operator:
        -D = H^{⊗n} · D_0 · H^{⊗n}
        """
        # Apply Hadamard to all data qubits
        self.qc.h(range(self.n_qubits))

        # Apply D_0
        self._apply_core_grover_diffusion()

        # Apply Hadamard to all data qubits
        self.qc.h(range(self.n_qubits))

    def _grover_iterations(self) -> None:
        for _ in range(self.iterations):
            self.grover_oracle()
            self.grover_diffusion()

    def grover_circuit(self) -> None:
        # Prepare ancilla in |–⟩ = H·X|0⟩
        self.qc.x(self.n_qubits)
        self.qc.barrier()
        # Initialize data qubits in superposition, and oracle to be |->
        self.qc.h(range(self.n_qubits + 1))
        self.qc.barrier()

        # Grover Iterations
        self._grover_iterations()

    def run(self) -> None:
        self.grover_circuit()

    def measure(self, shots: int = 1024) -> dict:
        self.qc.measure(range(self.n_qubits), range(self.n_qubits))
        simulator = AerSimulator()
        result = simulator.run(self.qc, shots=shots).result()
        counts = result.get_counts()
        return dict(counts)
