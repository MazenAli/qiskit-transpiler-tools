# -*- coding: utf-8 -*-
"""
Qiskit passmanagers for dynamic decoupling on IBM backends.
"""

from abc import ABC, abstractmethod

from qiskit.providers.ibmq import IBMQBackend
from qiskit.circuit.library import XGate
from qiskit.transpiler import PassManager, InstructionDurations
from qiskit.transpiler.passes import PadDynamicalDecoupling, ALAPScheduleAnalysis


class DDPassManager(ABC):
    """Abstract class for assembling pass managers for dynamic decoupling."""
    
    def __init__(self) -> None:
        
        pass
    
    
    @abstractmethod
    def get_pass_manager(self) -> PassManager:
        """Returns the pass manager for DD.

        Returns
        -------
        PassManager
        """
        pass
    

class PassManager_DD_ALAP_XX(DDPassManager):
    """Class for assembling pass managers with ALAP scheduling and XX dynamic decoupling sequences.
    
    Parameters
    ----------
    backend : Target backend for DD instructions.
    """
    
    
    def __init__(self,
                 backend: IBMQBackend) -> None:
        self._backend = backend
        
        
    def get_pass_manager(self):
        """Returns the pass manager for DD.

        Returns
        -------
            ALAP passmanager with XX decoupling.
        """
        
        durations        = InstructionDurations.from_backend(self._backend)
        dd_sequence      = [XGate(), XGate()]
        pulse_alignment  = self._backend.configuration().timing_constraints['pulse_alignment']
        pm               = PassManager([ALAPScheduleAnalysis(durations),
                                        PadDynamicalDecoupling(durations,
                                        dd_sequence,
                                        pulse_alignment=pulse_alignment)])
        
        return pm

        
    @property
    def backend(self):
        """Backend target for pass manager."""
        return self._backend
    
    
    @backend.setter
    def backend(self, backend):
        self._backend = backend
