# Design Document: RISC-V Instruction Set Explorer

## Overview

The project implements three tiers of functionality:

1. Parsing a RISC-V instruction dictionary and grouping instructions by extension.
2. Cross-referencing those extensions with the official RISC-V ISA manual.
3. Generating a graph of extension relationships and running unit tests.

The code is structured into separate modules, each responsible for one tier or a cross-cutting concern. All data is cached locally to avoid redundant network operations.

## Module Organization

- `main.py` – command line interface, orchestrates the three tiers.
- `src/instruction_parser.py` – Tier 1: downloads and parses `instr_dict.json`.
- `src/manual_scanner.py` – Tier 2: clones the ISA manual and scans AsciiDoc files for extension names.
- `src/cross_reference.py` – Tier 2: compares extension sets from JSON and the manual.
- `src/visualization.py` – Tier 3: builds a graph of shared instructions and exports visualisations.
- `tests/test_all.py` – unit and integration tests.

## Tier 1: Instruction Set Parsing

### Responsibilities

- Fetch `instr_dict.json` from the riscv-extensions-landscape GitHub repository.
- Cache the file locally (default location: `data/instr_dict.json`).
- Parse the JSON and extract for each instruction: its name and a list of extension tags.
- Build two indexes:
  - `instructions`: mapping from instruction name to a list of extensions.
  - `extensions`: mapping from extension name to a list of instruction names.
- Identify instructions that belong to more than one extension (multi‑extension instructions).

### Normalisation

- Extension names are converted to lower case.
- The `rv_` prefix (e.g., `rv_i`, `rv_zba`) is removed to produce a canonical form (e.g., `i`, `zba`).
- No other transformations are applied at this stage.

### Error Handling

- If a required field (`name`, `extensions`) is missing, the instruction is skipped.
- Malformed JSON entries are caught; parsing continues for the rest of the file.
- Network errors fall back to the cached copy if available.

## Tier 2: Cross‑Reference with ISA Manual

### ManualScanner

The `ManualScanner` class manages the local clone of the official RISC‑V ISA manual.

- `clone_manual()`: clones `https://github.com/riscv/riscv-isa-manual` into `data/riscv-isa-manual` if not already present.
- `scan_manual()`: walks the `src/` directory of the manual, reads all `.adoc` files, and extracts extension names using pattern matching.

#### Extraction patterns

The scanner looks for extension names in:

- AsciiDoc anchors: `[[Zba]]`
- AsciiDoc attributes: `:Zba:`
- Text patterns: `the Zba extension`, `Zba extension`
- File names: `zba.adoc` → `zba`
- RISC‑V prefixed forms: `rv_zba`, `RV32I`

All found names are normalised using the same lower‑case and `rv_` stripping rules as in Tier 1.

### CrossReferencer

- Takes the set of extensions from Tier 1 (`json_extensions`) and the set from the manual (`manual_extensions`).
- Normalises both sets (already done, but ensures consistency).
- Computes:
  - Common extensions (present in both).
  - Extensions only in JSON.
  - Extensions only in the manual.
- Prints a summary report with counts and lists.

## Tier 3: Graph Generation and Testing

### ExtensionGraph

The `ExtensionGraph` class builds an undirected graph where:

- Nodes are extension names.
- An edge exists between two extensions if they share at least one instruction (i.e., the same instruction belongs to both extensions).

#### Graph construction

- From the parsed instruction data, each instruction’s extension list is examined.
- For every pair of extensions in that list, an edge is recorded.
- The adjacency list is stored as a dictionary: `extension -> set(neighbours)`.
- Shared instruction counts are tracked optionally.

#### Exports

- Console output: connected components, per‑node neighbour lists, and edge statistics.
- Graphviz DOT file (`data/extension_graph.dot`) for rendering with `dot`.
- CSV adjacency matrix (`data/extension_adjacency.csv`) for external analysis.

### Testing

Unit tests are implemented using Python’s `unittest` framework. They cover:

- Parsing of correct and malformed JSON.
- Normalisation of extension names.
- Multi‑extension instruction detection.
- Manual scanner pattern extraction (with mock file content).
- Cross‑reference set comparisons.
- Graph adjacency and connected component logic.
- End‑to‑end integration of all three tiers.

Tests are isolated using temporary directories and mock objects to avoid network calls and filesystem side effects.

## Data Flow

1. `main.py` calls `InstructionParser.fetch_instr_dict()` to obtain the JSON file.
2. `InstructionParser.parse_instructions()` builds the internal data structures.
3. If Tier 2 is requested, `ManualScanner.clone_manual()` ensures the manual is present, then `scan_manual()` returns a set of extensions.
4. `CrossReferencer.cross_reference()` compares the two sets and prints the report.
5. If Tier 3 is requested, `ExtensionGraph` uses the parsed instructions to build the graph and produce outputs.

All large assets (JSON cache, manual clone) are stored under the `data/` directory and reused across runs.

## Edge Case Handling

### Parsing

- Missing or empty `extensions` field → instruction skipped.
- Duplicate instruction names → last occurrence overwrites.
- Null values in JSON → treated as absent.

### Manual Scanning

- Non‑AsciiDoc files or unreadable files → skipped with warning.
- Encoding errors → UTF‑8 with `errors='ignore'`.
- Common words matched by regex (e.g., “the”, “and”) → filtered out via a validation list of known RISC‑V extension patterns.

### Cross‑reference

- Case differences → resolved by lower‑casing.
- Prefix variations (`rv_`, `RV32`, `RV64`) → stripped.
- Version suffixes (e.g., `zba1`) → stripped to base name.
- Extensions present only in one source → reported, not treated as error.

### Graph building

- Instructions with a single extension → no edges created.
- Self‑loops ignored.
- Large numbers of multi‑extension instructions → still O(n) in instruction count.

## Performance Considerations

- Parsing: O(i) where i = number of instructions.
- Manual scanning: I/O bound; clone performed once.
- Graph construction: O(e) where e = total pairs of extensions per instruction.
- Memory: stores instruction lists per extension; typical usage < 100 MB.

## Limitations

- Manual scanning relies on regular expressions; non‑standard or very new extension names may not be detected.
- The ISA manual clone is not updated incrementally; a `--refresh` flag is required to re‑clone.
- Graph visualisation requires an external tool (Graphviz) to convert the DOT file to an image.
- The instruction dictionary JSON structure is assumed to match the one from riscv-extensions-landscape; other schemas are not supported.

## Future Work (Not Included)

- Use an official machine‑readable extension database instead of regex.
- Incremental updates for the manual repository.
- Interactive HTML graph visualisation.
- Configurable JSON schema mapping.

---

**Document Version**: 2.0  
**Last Updated**: 2025  
**Status**: Final