from qiskit import QuantumCircuit
from qiskit.providers.aer import AerSimulator
from qiskit_transpiler_tools.dd_passmanager import PassManager_DD_ALAP_XX
from qiskit_transpiler_tools.transpiler import (TranspilerSabreMapomaticDD,
                                                transpile_cost_depthcnot)

# fixture
SIM_BACKEND = AerSimulator()
TWO_CNOTS   = QuantumCircuit(2)
TWO_CNOTS.cx(0, 1)
TWO_CNOTS.cx(1, 0)


# tests
def test_pass_manager(backend = SIM_BACKEND):
    
    try:
        pm = PassManager_DD_ALAP_XX(backend)
    except Exception as exc:
        assert False, f"PassManager_DD_ALAP_XX constructor raised an exception {exc}"
    
    assert (pm is not None), "PassManager_DD_ALAP_XX constructor returns None!"
    

def test_transpile_cost(qc = TWO_CNOTS):
    cost = transpile_cost_depthcnot(TWO_CNOTS)
    
    assert (cost == 42.0), "Default cost of transpile_cost_depthcnot for two cnots not equal to 42.0!"
    

def test_default_transpiler(backend = SIM_BACKEND, qc = TWO_CNOTS):
    
    qc_trans      = None
    qc_trans_list = None
    
    try:
        transpiler    = TranspilerSabreMapomaticDD(backend)
        qc_trans      = transpiler.transpile(qc)
        qc_trans_list = transpiler.transpile([qc])
    except Exception as exc:
        assert False, f"TranspilerSabreMapomaticDD raised an exception {exc}"
        
    assert qc_trans is not None, "TranspilerSabreMapomaticDD transpile output is None!"
    assert qc_trans_list is not None, "TranspilerSabreMapomaticDD transpile output is None!"
    assert isinstance(qc_trans_list, list), "TranspilerSabreMapomaticDD transpile returned non-list for list input!"
    
    