# RISC-V Instruction Set Explorer

A tool for analyzing RISC-V instruction sets across three tiers: parsing an instruction dictionary, cross-referencing with the official ISA manual, and generating extension relationship graphs.

## Overview

This project implements the three required tiers of the RISC-V Mentorship Coding Challenge.

- Tier 1: Instruction set parsing and grouping by extension.
- Tier 2: Cross-reference with the ISA manual.
- Tier 3 (bonus): Unit tests and visualisation of extension relationships.

## Features

### Tier 1 – Instruction Set Parsing
- Downloads `instr_dict.json` from the riscv-extensions-landscape repository.
- Parses instruction entries and groups them by extension tags.
- Prints a summary table with extension names, instruction counts, and an example instruction.
- Identifies instructions that belong to multiple extensions.

### Tier 2 – Cross-Reference with ISA Manual
- Clones the official RISC-V ISA manual repository.
- Scans AsciiDoc source files for extension references.
- Compares extensions found in the JSON with those in the manual.
- Normalises naming variations (e.g., `rv_zba` vs `Zba`).
- Reports matches, JSON-only extensions, and manual-only extensions.

### Tier 3 – Visualisation and Testing
- Provides unit tests for parsing, grouping, cross-reference logic, and graph generation.
- Generates a text-based graph of extension relationships.
- Exports a Graphviz DOT file for external rendering.
- Exports a CSV adjacency matrix for further analysis.
- Computes connected components of the extension graph.

## Requirements

- Python 3.7 or later
- Git (to clone the ISA manual)
- Internet connection (for initial data fetch)

## Installation

Clone the repository and install dependencies.
# riscv-instruction-set-explorer

## Sample Output

A representative CLI transcript is available in [sample_output.txt](sample_output.txt).
