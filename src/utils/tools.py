from qiskit import (ClassicalRegister, QuantumCircuit, QuantumRegister,
                    transpile)
from qiskit.circuit import Qubit
from qiskit.circuit.library.arithmetic import DraperQFTAdder, RGQFTMultiplier
from qiskit_aer import AerSimulator


def to_ranges(nums):
    if not nums:
        return []

    ranges = []
    start = prev = nums[0]

    for n in nums[1:]:
        if n == prev + 1:
            # Continue the current range
            prev = n
        else:
            # Close the previous range and start a new one
            ranges.append((start, prev))
            start = prev = n
    # Append the last range
    ranges.append((start, prev))
    return ranges


def get_register_by_name(
    qc: QuantumCircuit, name: str, quantum_register: bool = True
) -> QuantumRegister | ClassicalRegister:
    regs: list = qc.qregs if quantum_register else qc.cregs
    for reg in regs:
        if reg.name == name:
            return reg
    raise ValueError(f"Register {name} not found")


def get_index_from_quantum_circuit(
    qc: QuantumCircuit, name: str, quantum_register=True
) -> tuple[int]:
    qr = get_register_by_name(qc, name, quantum_register)
    if len(qr) > 0:
        return qc.find_bit(qr[0]).index, qc.find_bit(qr[-1]).index


def split_by_lengths(s: str, spans: list[str]) -> str:
    substrings = []
    start = 0
    for length in spans:
        substrings.append(s[start : start + length])
        start += length
    return " ".join(substrings)


def measure_quantum_indices(
    # one register
    qc: QuantumCircuit,
    indices: list[tuple[int]] | tuple[int],
    shots: int = 1024,
    num_qubits: int = 28,
):
    if isinstance(indices, int):
        indices = [indices]

    output = []
    for span_indx in indices:
        i, j = span_indx
        temp_idxs = list(range(i, j + 1))
        temp_qc = qc.copy()

        cbits = ClassicalRegister(len(temp_idxs))
        temp_qc.add_register(cbits)
        temp_qc.measure(temp_idxs, cbits)
        # Run with AerSimulator
        simulator = AerSimulator(n_qubits=num_qubits)
        temp_qc = transpile(temp_qc, backend=simulator)
        result = simulator.run(temp_qc, shots=shots).result()
        counts = dict(result.get_counts())
        k = list(counts.keys())[0].split(" ")[0]
        output.append(k)
    output.reverse()
    return "".join(output)


def measure_quantum_register(
    qc: QuantumCircuit,
    names: list[str] | str,
    shots: int = 1024,
    num_qubits: int = 28,
):
    if isinstance(names, str):
        names = [names]
    temp_qc = qc.copy()
    idxs = []
    spans = []
    for name in names:
        i, j = get_index_from_quantum_circuit(temp_qc, name, quantum_register=True)
        temp_idxs = list(range(i, j + 1))
        spans.append(len(temp_idxs))
        idxs += temp_idxs

    if len(idxs) == 0:
        return
    cbits = ClassicalRegister(len(idxs))
    temp_qc.add_register(cbits)
    temp_qc.measure(idxs, cbits)
    # Run with AerSimulator
    simulator = AerSimulator(n_qubits=num_qubits)
    temp_qc = transpile(temp_qc, backend=simulator)

    result = simulator.run(temp_qc, shots=shots).result()
    counts = dict(result.get_counts())
    result_counts = {
        split_by_lengths(k.split(" ")[0], spans): v for k, v in counts.items()
    }
    return result_counts


def placeholder_numerate(qc: QuantumCircuit, name_placeholder: str) -> int | str:
    lst = [reg for reg in qc.qregs if reg.name.startswith(name_placeholder)]
    return len(lst) if len(lst) > 0 else ""


def create_placeholder_register(
    qc: QuantumCircuit, placeholder_name: str, qubits: int
) -> tuple[QuantumRegister, str]:
    placeholder_num = placeholder_numerate(qc, placeholder_name)
    name = f"{placeholder_name}{placeholder_num}"
    return QuantumRegister(qubits, name=name), name


def addition(
    qc: QuantumCircuit,
    first_registers_names: list[str],
    first_register_name: str,
    second_registers_names: list[str],
    second_register_name: str,
    name: str | None = None,
    is_borrower: bool = True,
) -> tuple[QuantumRegister, int]:
    first_registers: list[QuantumRegister] = [
        get_register_by_name(qc, first_register_name, quantum_register=True)
        for first_register_name in first_registers_names
    ]
    first_register_qubits: list[Qubit] = [
        qubit for qr in first_registers for qubit in qr
    ]
    second_registers: list[QuantumRegister] = [
        get_register_by_name(qc, second_register_name, quantum_register=True)
        for second_register_name in second_registers_names
    ]
    second_register_qubits: list[Qubit] = [
        qubit for qr in second_registers for qubit in qr
    ]
    first_registers_size: int = sum([len(qr) for qr in first_registers])
    second_registers_size: int = sum([len(qr) for qr in second_registers])

    diff_len = abs(first_registers_size - second_registers_size)
    max_qubits = max(first_registers_size, second_registers_size)

    # Quantum registers
    if is_borrower:
        a_borrower, a_borrower_name = create_placeholder_register(
            qc, f"{first_register_name}_borrower", 1
        )
        b_borrower, b_borrower_name = create_placeholder_register(
            qc, f"{second_register_name}_borrower", 1
        )
    else:
        a_borrower, a_borrower_name = create_placeholder_register(
            qc, f"{first_register_name}_borrower", 0
        )
        b_borrower, b_borrower_name = create_placeholder_register(
            qc, f"{second_register_name}_borrower", 0
        )

    adder = DraperQFTAdder(max_qubits + 1, "fixed").decompose()
    if first_registers_size >= second_registers_size:
        b_pad, b_pad_name = create_placeholder_register(
            qc, f"{second_register_name}_pad", diff_len
        )
        qc.add_register(a_borrower, b_borrower, b_pad)
        qc.append(
            adder,
            first_register_qubits[:]
            + a_borrower[:]
            + second_register_qubits[:]
            + b_pad[:]
            + b_borrower[:],
        )

        second_register_full_qubits = (
            second_register_qubits[:] + b_pad[:] + b_borrower[:]
        )

    else:
        a_pad, a_pad_name = create_placeholder_register(
            qc, f"{first_register_name}_pad", diff_len
        )
        qc.add_register(a_borrower, b_borrower, a_pad)
        qc.append(
            adder,
            first_register_qubits[:]
            + a_pad[:]
            + a_borrower[:]
            + second_register_qubits[:]
            + b_borrower[:],
        )
        second_register_full_qubits = second_register_qubits[:] + b_borrower[:]

    if not name:
        return qc, second_register_full_qubits
    # copying b-register to sum-register
    sum_reg, sum_reg_name = create_placeholder_register(
        qc, name, max_qubits + 1
    )  # sum_reg should have enough qubits for sum (n+1 for overflow)
    qc.add_register(sum_reg)

    second_register_indices = [
        qc.find_bit(qubit).index for qubit in second_register_qubits
    ]
    sum_register_indices = [qc.find_bit(qubit).index for qubit in sum_reg]

    second_borrower_index = get_index_from_quantum_circuit(
        qc, b_borrower_name, quantum_register=True
    )[0]
    second_register_pad_indices = [qc.find_bit(qubit).index for qubit in b_pad]
    second_register_indices += second_register_pad_indices
    second_register_indices.append(second_borrower_index)

    for i, j in zip(second_register_indices, sum_register_indices):
        qc.cx(i, j)  # copy to register c
    qc.barrier()
    adder = DraperQFTAdder(max_qubits + 1, "fixed").decompose()
    # undo the addition
    if first_registers_size >= second_registers_size:
        qc.append(
            adder.inverse(),
            first_register_qubits[:]
            + a_borrower[:]
            + second_register_qubits[:]
            + b_pad[:]
            + b_borrower[:],
        )
    else:
        qc.append(
            adder.inverse(),
            first_register_qubits[:]
            + a_pad[:]
            + a_borrower[:]
            + second_register_qubits[:]
            + b_borrower[:],
        )
    return qc, sum_register_indices


def addition_idx(
    qc: QuantumCircuit,
    first_registers_idxs: list[int],
    second_registers_idxs: list[int],
    name: str | None = None,
    is_borrower: bool = True,
):
    first_registers_size = len(first_registers_idxs)
    second_registers_size = len(second_registers_idxs)
    first_registers_qubits = [qc.qubits[i] for i in first_registers_idxs]
    second_registers_qubits = [qc.qubits[i] for i in second_registers_idxs]

    diff_len = abs(first_registers_size - second_registers_size)
    max_qubits = max(first_registers_size, second_registers_size)

    # Quantum registers
    if is_borrower:
        a_borrower, a_borrower_name = create_placeholder_register(
            qc, "first_reg_borrower", 1
        )
        b_borrower, b_borrower_name = create_placeholder_register(
            qc, "second_reg_borrower", 1
        )
    else:
        a_borrower, a_borrower_name = create_placeholder_register(
            qc, "first_reg_borrower", 0
        )
        b_borrower, b_borrower_name = create_placeholder_register(
            qc, "second_reg_borrower", 0
        )

    # addition
    adder = DraperQFTAdder(max_qubits + 1, "fixed").decompose()
    inv = adder.inverse()

    if first_registers_size >= second_registers_size:
        b_pad, b_pad_name = create_placeholder_register(qc, "pad", diff_len)
        qc.add_register(a_borrower, b_borrower, b_pad)
        qc.append(
            adder,
            first_registers_qubits[:]
            + a_borrower[:]
            + second_registers_qubits[:]
            + b_pad[:]
            + b_borrower[:],
        )
        second_register_full_qubits = (
            second_registers_qubits[:] + b_pad[:] + b_borrower[:]
        )

    else:
        a_pad, a_pad_name = create_placeholder_register(qc, "pad", diff_len)
        qc.add_register(a_borrower, b_borrower, a_pad)
        qc.append(
            adder,
            first_registers_qubits[:]
            + a_pad[:]
            + a_borrower[:]
            + second_registers_qubits[:]
            + b_borrower[:],
        )
        second_register_full_qubits = second_registers_qubits[:] + b_borrower[:]
    second_register_full_qubits_idxs = [
        qc.find_bit(q).index for q in second_register_full_qubits
    ]
    if not name:
        return qc, second_register_full_qubits_idxs
    # copying b-register to sum-register
    sum_reg, sum_reg_name = create_placeholder_register(
        qc, name, max_qubits + 1
    )  # sum_reg should have enough qubits for sum (n+1 for overflow)
    qc.add_register(sum_reg)

    sum_register_indices = [qc.find_bit(qubit).index for qubit in sum_reg]
    second_borrower_index = get_index_from_quantum_circuit(
        qc, b_borrower_name, quantum_register=True
    )[0]
    second_register_pad_indices = [qc.find_bit(qubit).index for qubit in b_pad]
    second_register_full_qubits_idxs += second_register_pad_indices
    second_register_full_qubits_idxs.append(second_borrower_index)
    for i, j in zip(second_register_full_qubits_idxs, sum_register_indices):
        qc.cx(i, j)  # copy to register c
    qc.barrier()

    # undo the addition
    if first_registers_size >= second_registers_size:
        qc.append(
            inv,
            first_registers_qubits[:]
            + a_borrower[:]
            + second_registers_qubits[:]
            + b_pad[:]
            + b_borrower[:],
        )
    else:
        qc.append(
            adder.inverse(),
            first_registers_qubits[:]
            + a_pad[:]
            + a_borrower[:]
            + second_registers_qubits[:]
            + b_borrower[:],
        )
    return qc, sum_register_indices


def subtraction_idx(
    qc: QuantumCircuit,
    first_registers_idxs: list[int],
    second_registers_idxs: list[int],
    name: str | None = None,
    is_borrower: bool = True,
):
    first_registers_size = len(first_registers_idxs)
    second_registers_size = len(second_registers_idxs)
    first_registers_qubits = [qc.qubits[i] for i in first_registers_idxs]
    second_registers_qubits = [qc.qubits[i] for i in second_registers_idxs]

    diff_len = abs(first_registers_size - second_registers_size)
    max_qubits = max(first_registers_size, second_registers_size)

    # Quantum registers
    if is_borrower:
        a_borrower, a_borrower_name = create_placeholder_register(
            qc, "first_reg_borrower", 1
        )
        b_borrower, b_borrower_name = create_placeholder_register(
            qc, "second_reg_borrower", 1
        )
    else:
        a_borrower, a_borrower_name = create_placeholder_register(
            qc, "first_reg_borrower", 0
        )
        b_borrower, b_borrower_name = create_placeholder_register(
            qc, "second_reg_borrower", 0
        )

    inv = DraperQFTAdder(max_qubits + 1, "fixed").decompose()
    adder = DraperQFTAdder(max_qubits + 1, "fixed").decompose().inverse()

    if first_registers_size >= second_registers_size:
        b_pad, b_pad_name = create_placeholder_register(qc, "pad", diff_len)
        qc.add_register(a_borrower, b_borrower, b_pad)
        qc.append(
            adder,
            second_registers_qubits[:]
            + b_pad[:]
            + b_borrower[:]
            + first_registers_qubits[:]
            + a_borrower[:],
        )
        first_register_full_qubits = first_registers_qubits[:] + a_borrower[:]
        a_pad = None
    else:
        a_pad, a_pad_name = create_placeholder_register(qc, "pad", diff_len)
        qc.add_register(a_borrower, b_borrower, a_pad)
        qc.append(
            adder,
            second_registers_qubits[:]
            + b_borrower[:]
            + first_registers_qubits[:]
            + a_pad[:]
            + a_borrower[:],
        )
        first_register_full_qubits = (
            first_registers_qubits[:] + a_pad[:] + a_borrower[:]
        )

    first_register_full_qubits_idxs = [
        qc.find_bit(q).index for q in first_register_full_qubits
    ]
    if not name:
        return qc, first_register_full_qubits_idxs
    # copying b-register to sum-register
    sum_reg, sum_reg_name = create_placeholder_register(
        qc, name, max_qubits + 1
    )  # sum_reg should have enough qubits for sum (n+1 for overflow)
    qc.add_register(sum_reg)

    sum_register_indices = [qc.find_bit(qubit).index for qubit in sum_reg]
    first_borrower_index = get_index_from_quantum_circuit(
        qc, a_borrower_name, quantum_register=True
    )[0]

    if a_pad:
        first_register_pad_indices = [qc.find_bit(qubit).index for qubit in a_pad]
    else:
        first_register_pad_indices = []
    first_register_full_qubits_idxs += first_register_pad_indices
    first_register_full_qubits_idxs.append(first_borrower_index)
    for i, j in zip(first_register_full_qubits_idxs, sum_register_indices):
        qc.cx(i, j)  # copy to register c
    qc.barrier()

    # undo the addition
    if first_registers_size >= second_registers_size:
        qc.append(
            inv,
            second_registers_qubits[:]
            + b_pad[:]
            + b_borrower[:]
            + first_registers_qubits[:]
            + a_borrower[:],
        )
    else:
        qc.append(
            adder.inverse(),
            second_registers_qubits[:]
            + b_borrower[:]
            + first_registers_qubits[:]
            + a_pad[:]
            + a_borrower[:],
        )
    return qc, sum_register_indices


def multiplication_idx(
    qc: QuantumCircuit,
    first_registers_idxs: list[int],
    second_registers_idxs: list[int],
    name: str = "product",
) -> QuantumRegister:
    first_registers_size = len(first_registers_idxs)
    second_registers_size = len(second_registers_idxs)
    first_registers_qubits = [qc.qubits[i] for i in first_registers_idxs]
    second_registers_qubits = [qc.qubits[i] for i in second_registers_idxs]

    diff_len = abs(first_registers_size - second_registers_size)
    num_qubits = max(first_registers_size, second_registers_size)

    # cl_res = ClassicalRegister(2*num_qubits)
    prod_reg = QuantumRegister(2 * num_qubits, name)
    prod_reg, prod_reg_name = create_placeholder_register(
        qc, name, 2 * num_qubits
    )  # prod_reg should have enough qubits for product

    if first_registers_size >= second_registers_size:
        a_pad, a_pad_name = create_placeholder_register(qc, "first_pad", 0)
        b_pad, b_pad_name = create_placeholder_register(qc, "second_pad", diff_len)
    else:
        a_pad, a_pad_name = create_placeholder_register(qc, "first_pad", diff_len)
        b_pad, b_pad_name = create_placeholder_register(qc, "second_pad", 0)

    qc.add_register(a_pad, b_pad)
    qc.add_register(prod_reg)
    # qc.add_register(cl_res)
    # print(qc.qregs)
    qc.append(
        RGQFTMultiplier(num_qubits, 2 * num_qubits),
        first_registers_qubits[:]
        + list(a_pad)
        + second_registers_qubits[:]
        + list(b_pad)
        + list(prod_reg),
    )
    prod_register_indices = [qc.find_bit(qubit).index for qubit in prod_reg]
    return qc, prod_register_indices


def GT_gate_idx(
    qc: QuantumCircuit,
    first_registers_idxs: list[int],
    second_registers_idxs: list[int],
    name: str = "IsGreater",
) -> QuantumCircuit:
    """
    The GT Gate will be two main parts, and then uncompute these two parts.
    The first part is to apply CX gate on a and b registers qubit by qubit.
    Then, applying multi-controlled X gate with the output qubit.
    This quantum circuit is followed by the publication:
        Grover Search for Portfolio Selection - A. Ege Yilmaz, Stefan Stettler, Thomas Ankenbrand and Urs Rhyner
        https://arxiv.org/pdf/2308.13063
    """
    first_registers_size = len(first_registers_idxs)
    second_registers_size = len(second_registers_idxs)
    first_registers_qubits = [qc.qubits[i] for i in first_registers_idxs]
    second_registers_qubits = [qc.qubits[i] for i in second_registers_idxs]

    diff_len = abs(first_registers_size - second_registers_size)
    # num_qubits = max(first_registers_size, second_registers_size)

    if first_registers_size >= second_registers_size:
        a_pad, a_pad_name = create_placeholder_register(qc, "first_pad", 0)
        b_pad, b_pad_name = create_placeholder_register(qc, "second_pad", diff_len)
    else:
        a_pad, a_pad_name = create_placeholder_register(qc, "first_pad", diff_len)
        b_pad, b_pad_name = create_placeholder_register(qc, "second_pad", 0)

    is_greater_reg, is_greater_reg_name = create_placeholder_register(qc, name, 1)

    qc.add_register(a_pad, b_pad, is_greater_reg)
    a_pad_start_indices: None | tuple[int] = get_index_from_quantum_circuit(
        qc, a_pad_name, quantum_register=True
    )
    b_pad_start_indices: None | tuple[int] = get_index_from_quantum_circuit(
        qc, b_pad_name, quantum_register=True
    )

    is_greater_reg_index = get_index_from_quantum_circuit(
        qc, is_greater_reg_name, quantum_register=True
    )[0]
    if a_pad_start_indices:
        full_a_indices: list[int] = first_registers_idxs + list(
            range(a_pad_start_indices[0], a_pad_start_indices[0] + len(a_pad))
        )
    else:
        full_a_indices: list[int] = first_registers_idxs
    if b_pad_start_indices:
        full_b_indices: list[int] = second_registers_idxs + list(
            range(b_pad_start_indices[0], b_pad_start_indices[0] + len(b_pad))
        )
    else:
        full_b_indices = second_registers_idxs
    # # First Part
    for i, j in zip(reversed(full_a_indices), reversed(full_b_indices)):
        qc.cx(i, j)
    qc.barrier()
    # Second Part
    pair_indices = list(zip(reversed(full_a_indices), reversed(full_b_indices)))
    b_control_bits = []
    for i, idx in enumerate(pair_indices):
        a_idx, b_idx = idx
        b_control_bits.append(b_idx)
        controlled_qubits = []
        controlled_qubits.append(a_idx)
        controlled_qubits += b_control_bits
        qc.mcx(controlled_qubits, is_greater_reg_index)
        qc.x(b_idx)
    qc.barrier()
    # uncompute Second part
    for b_idx in full_b_indices:
        qc.x(b_idx)
        qc.barrier()
    # # uncompute First part
    for i, j in zip(full_a_indices, full_b_indices):
        qc.cx(i, j)
        qc.barrier()
    is_greater_register_indices = [qc.find_bit(qubit).index for qubit in is_greater_reg]
    return qc, is_greater_register_indices
