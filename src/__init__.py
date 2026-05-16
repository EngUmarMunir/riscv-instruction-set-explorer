"""
RISC-V Instruction Set Explorer - Source Modules

Modules:
- instruction_parser: Tier 1 - Parse RISC-V instructions
- manual_scanner: Tier 2 - Scan ISA manual
- cross_reference: Tier 2 - Cross-reference data
- visualization: Tier 3 - Generate visualizations
"""

__version__ = "1.0.0"
__author__ = "RISC-V Mentorship Participant"

from .instruction_parser import InstructionParser, Instruction
from .manual_scanner import ManualScanner
from .cross_reference import CrossReferencer, CrossReferenceReport
from .visualization import ExtensionGraph, GraphExporter

__all__ = [
    'InstructionParser',
    'Instruction',
    'ManualScanner',
    'CrossReferencer',
    'CrossReferenceReport',
    'ExtensionGraph',
    'GraphExporter',
]
