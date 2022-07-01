"""
Qiskit transpilation pipeline for IBM backends.
"""

from abc import ABC, abstractmethod
from typing import Union, List, Optional, Callable

import numpy as np
from qiskit import compiler, QuantumCircuit
from qiskit.providers.ibmq import IBMQBackend
import mapomatic

from qiskit_transpiler_tools.dd_passmanager import (DDPassManager,
                                                    PassManager_DD_ALAP_XX)



class Transpiler(ABC):
    """Abstract class for transpilers.
    Basic functionality is to transpile.
    """
    
    def __init__(self) -> None:
        
        pass

        
    @abstractmethod
    def transpile(self,
                  circuits: Union[QuantumCircuit, List[QuantumCircuit]]) -> Union[QuantumCircuit, List[QuantumCircuit]]:
        """Transpile circuits for backend.

        Parameters
        ----------
        circuits : Circuit(s) to transpile.

        Returns
        -------
        Transpiled circuits.
        """
        
        pass
        
    
        
class TranspilerSabreMapomaticDD(Transpiler):
    """Transpilation pipeline for IBM backends.
    Includes level 3 SABRE swap optimization, mapomatic noise-sensitive layout selection and elementary XX dynamic decoupling.
        
    Example 1:
        transpiler = TranspilerSabreMapomaticDD(backend)
        trans_qc   = transpiler.transpile(qc)
        
    Example 2:
        transpiler = TranspilerSabreMapomaticDD(backend, num_transpilations=20, apply_dd=True)
        trans_qc   = transpiler.transpile(qc)
        
    Example 3:
        options    = {'optimization_level': 1,
                      'num_transpilations': 5,
                      'cost_transpile'    : my_cost_transpile,
                      'apply_mapomatic'   : my_cost_mapomatic,
                      'apply_dd'          : True,
                      'dd_passmanager'    : my_dd_pm}
        
        transpiler = TranspilerSabreMapomaticDD(backend, **options)
        trans_qc   = transpiler.transpile(qc)
    
    
    Parameters
    ----------
    backend : Target backend for transpilation.
    optimization_level : Connectivity layout optimization, levels 0 - 3 available.
    num_transpilations : Number of times transpilation is repeated, best layout selected.
    seed_transpiler : Each run can yield different layouts, seed for reproducibility, input is a list of size num_transpilations.
    cost_transpile : Score function for layouts, default is a weighted sum = 1*depth + 20*num_cnots.
    apply_mapomatic : Noise-sensitive layout optimization.
    cost_mapomatic : Score function for mapomatic, default is mapomatic default.
    apply_dd : Apply dynamic decoupling.
    dd_passmanager : Pass manager for DD, default is ALAP scheduling with XX decoupling.
    """
    
    
    def __init__(self,
                 backend:            IBMQBackend,
                 optimization_level: Optional[int] = 0,
                 num_transpilations: Optional[int] = 1,
                 seed_transpiler:    Optional[List[int]] = None,
                 cost_transpile:     Optional[Callable]  = None,
                 apply_mapomatic:    Optional[bool] = False,
                 cost_mapomatic:     Optional[Callable] = None,
                 apply_dd:           Optional[bool] = False,
                 dd_passmanager:     Optional[DDPassManager] = None) -> None:
        
        self._backend             = backend
        self._optimization_level  = optimization_level
        self._num_transpilations  = num_transpilations
        self._seed_transpiler     = seed_transpiler
        self._cost_transpile      = cost_transpile
        self._apply_mapomatic     = apply_mapomatic
        self._cost_mapomatic      = cost_mapomatic
        self._apply_dd            = apply_dd
        self._dd_passmanager      = dd_passmanager
    
    
    def transpile(self,
                  circuits: Union[QuantumCircuit, List[QuantumCircuit]]) -> Union[QuantumCircuit, List[QuantumCircuit]]:
        """Transpile circuits for target backend.

        Parameters
        ----------
        circuits : Circuit(s) to transpile.

        Returns
        -------
            Transpiled circuits.
        """
        
        # unify to list format
        circuits_ = circuits
        if type(circuits) is not list:
            circuits_ = [circuits]
        
        backend = self._backend
            
        # options
        optimization_level = self._optimization_level
        num_transpilations = self._num_transpilations
        seed_transpiler    = self._seed_transpiler
        cost_transpile     = self._cost_transpile
        apply_mapomatic    = self._apply_mapomatic
        cost_mapomatic     = self._cost_mapomatic
        apply_dd           = self._apply_dd
        dd_passmanager     = self._dd_passmanager
        
        # default arguments
        if seed_transpiler is None:
            seed_transpiler = [None]*num_transpilations
        else:
            assert len(seed_transpiler) >= num_transpilations
        
        if cost_transpile is None:
            cost_transpile = transpile_cost_depthcnot
            
        if apply_dd and (dd_passmanager is None):
            dd_pm_xx       = PassManager_DD_ALAP_XX(self._backend)
            dd_passmanager = dd_pm_xx.get_pass_manager()
        
        # transpile for backend
        trans_circs = []
        num_circs   = len(circuits_)
        for i in range(num_circs):
            trans_qc = compiler.transpile([circuits_[i]]*num_transpilations,
                                          backend,
                                          optimization_level=optimization_level,
                                          seed_transpiler=seed_transpiler)
            costs    = np.array([cost_transpile(circ) for circ in trans_qc])
            best_pos = np.asarray(costs == min(costs)).nonzero()[0][0]
            trans_circs.append(trans_qc[best_pos])
        
        # apply mapomatic
        if apply_mapomatic:
            
            # deflate
            deflated = []
            for qc in trans_circs:
                small_qc = mapomatic.deflate_circuit(qc)
                deflated.append(small_qc)
            
            # select best layout and transpile again
            for i in range(num_circs):
                small_qc         = mapomatic.deflate_circuit(trans_circs[i])
                layouts          = mapomatic.matching_layouts(small_qc, backend)
                scores           = mapomatic.evaluate_layouts(small_qc, layouts,
                                                              backend,
                                                              cost_function=cost_mapomatic)
                best_layout      = scores[0][0]
                trans_circs[i]   = compiler.transpile(small_qc,
                                                      backend,
                                                      initial_layout=best_layout)
        
        # apply DD
        if apply_dd:
            for i in range(num_circs):
                trans_circs[i] = dd_passmanager.run(trans_circs[i])
            
        
        # return transpiled circuits in the same format as input
        if type(circuits) is not list:
            return trans_circs[0]
        
        return trans_circs

    
    @property
    def backend(self):
        """Backend target for transpilation."""
        return self._backend
    
    @backend.setter
    def backend(self, backend):
        self._backend = backend
      
        
        
def transpile_cost_depthcnot(circuit:      QuantumCircuit,
                             weight_depth: Optional[float] = 1.,
                             weight_cnot:  Optional[float] = 20.) -> float:
    """Function that returns the cost of the circuit
    based on a weighted sum of depth and number of cnots.
    
    Parameters
    ----------
    circuit : Circuit for which to compute the cost.
    weight_depth : Weight for depth. Default is 1.
    weight_cnot : Weight for number of cnots. Default is 20.
    
    Returns
    -------
        Cost of circuit.
    """
    
    num_cnots = 0
    if 'cx' in circuit.count_ops():
        num_cnots = circuit.count_ops()['cx']
    
    cost = weight_depth*circuit.depth() + weight_cnot*num_cnots
    
    return cost