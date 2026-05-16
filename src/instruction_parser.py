"""
Tier 1: RISC-V Instruction Set Parser

This module handles parsing and grouping of RISC-V instructions from instr_dict.json.
It provides functionality to:
- Load and parse instruction data from JSON
- Group instructions by extension tags
- Identify multi-extension instructions
- Generate formatted summary tables
"""

import json
import requests
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass


@dataclass
class Instruction:
    """Represents a single RISC-V instruction."""
    name: str
    extensions: List[str]
    description: str = ""


class InstructionParser:
    """Parser for RISC-V instruction dictionary JSON files."""
    
    # GitHub URL for the extensions landscape repository
    EXTENSIONS_REPO_URL = "https://raw.githubusercontent.com/rpsene/riscv-extensions-landscape/main/src"
    INSTR_DICT_PATH = "instr_dict.json"
    
    def __init__(self, data_dir: str = "./data"):
        """
        Initialize the instruction parser.
        
        Args:
            data_dir: Directory to cache downloaded files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.instructions: Dict[str, Instruction] = {}
        self.extensions: Dict[str, List[str]] = defaultdict(list)
        self.multi_ext_instructions: List[Tuple[str, List[str]]] = []
    
    def fetch_instr_dict(self, force_refresh: bool = False) -> str:
        """
        Fetch the instruction dictionary from GitHub or use cached version.
        
        Args:
            force_refresh: If True, always download from GitHub
            
        Returns:
            Path to the instruction dictionary file
        """
        local_path = self.data_dir / self.INSTR_DICT_PATH
        
        if local_path.exists() and not force_refresh:
            print(f"Using cached instruction dictionary: {local_path}")
            return str(local_path)
        
        try:
            url = f"{self.EXTENSIONS_REPO_URL}/{self.INSTR_DICT_PATH}"
            print(f"Downloading instruction dictionary from {url}...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            with open(local_path, 'w') as f:
                f.write(response.text)
            print(f"Saved to {local_path}")
            return str(local_path)
        except Exception as e:
            if local_path.exists():
                print(f"Download failed, using cached version: {e}")
                return str(local_path)
            raise
    
    def parse_instructions(self, instr_dict_path: str) -> None:
        """
        Parse instructions from the dictionary file.
        
        Args:
            instr_dict_path: Path to the instruction dictionary JSON file
        """
        print(f"Parsing instructions from {instr_dict_path}...")
        
        with open(instr_dict_path, 'r') as f:
            data = json.load(f)

        # Support both list-based fixtures and the real mnemonic-keyed JSON map.
        if isinstance(data, list):
            instruction_items = data
        elif isinstance(data, dict) and isinstance(data.get('instructions'), list):
            instruction_items = data.get('instructions', [])
        elif isinstance(data, dict):
            instruction_items = []
            for mnemonic, details in data.items():
                if isinstance(details, dict):
                    item = dict(details)
                    item.setdefault('name', mnemonic)
                    instruction_items.append(item)
        else:
            instruction_items = []

        for item in instruction_items:
            if not isinstance(item, dict):
                continue

            # Support multiple field name variations used across the challenge data.
            name = item.get('name') or item.get('mnemonic') or item.get('instruction')
            extensions = (
                item.get('extension')
                or item.get('extensions')
                or item.get('ext')
                or item.get('tags')
                or []
            )
            description = item.get('description') or item.get('desc') or ""

            if isinstance(extensions, str):
                extensions = [extensions]

            if name and extensions:
                # Normalize extension names to lowercase for consistency.
                normalized_exts = [ext.lower() if isinstance(ext, str) else str(ext)
                                   for ext in extensions]

                instruction = Instruction(
                    name=str(name).upper(),
                    extensions=normalized_exts,
                    description=str(description)
                )
                self.instructions[instruction.name] = instruction

                # Group by extension.
                for ext in normalized_exts:
                    self.extensions[ext].append(instruction.name)

                # Track multi-extension instructions.
                if len(normalized_exts) > 1:
                    self.multi_ext_instructions.append(
                        (instruction.name, normalized_exts)
                    )
        
        print(f"Parsed {len(self.instructions)} instructions across "
              f"{len(self.extensions)} extensions")
    
    def get_extension_summary(self) -> List[Tuple[str, int, str]]:
        """
        Generate summary of extensions with instruction counts and examples.
        
        Returns:
            List of (extension_name, instruction_count, example_mnemonic) tuples
        """
        summary = []
        for ext in sorted(self.extensions.keys()):
            instructions = self.extensions[ext]
            summary.append((
                ext,
                len(instructions),
                instructions[0]  # First instruction as example
            ))
        return summary
    
    def print_summary_table(self) -> None:
        """Print a formatted summary table of extensions."""
        print("\n" + "="*70)
        print("INSTRUCTION SET SUMMARY TABLE")
        print("="*70)
        print(f"{'Extension':<15} | {'Instructions':<15} | {'Example':<20}")
        print("-"*70)
        
        for ext, count, example in self.get_extension_summary():
            print(f"{ext:<15} | {count:<15} | {example:<20}")
        
        print("="*70)
        print(f"Total Extensions: {len(self.extensions)}")
        print(f"Total Instructions: {len(self.instructions)}")
        print(f"Multi-Extension Instructions: {len(self.multi_ext_instructions)}")
        print("="*70)
    
    def print_multi_extension_instructions(self) -> None:
        """Print instructions that belong to multiple extensions."""
        print("\n" + "="*70)
        print("INSTRUCTIONS WITH MULTIPLE EXTENSIONS")
        print("="*70)
        
        if not self.multi_ext_instructions:
            print("No instructions found with multiple extensions")
        else:
            for instr_name, exts in sorted(self.multi_ext_instructions):
                ext_str = ", ".join(exts)
                print(f"{instr_name:<20} | Extensions: {ext_str}")
        
        print("="*70)
    
    def get_multi_extension_instructions(self) -> List[Tuple[str, List[str]]]:
        """Return list of instructions with multiple extensions."""
        return self.multi_ext_instructions
    
    def get_extensions_dict(self) -> Dict[str, List[str]]:
        """Return the extensions dictionary."""
        return dict(self.extensions)
    
    def get_instructions_dict(self) -> Dict[str, Instruction]:
        """Return the instructions dictionary."""
        return self.instructions


def main():
    """Main entry point for instruction parser."""
    parser = InstructionParser(data_dir="./data")
    
    # Fetch and parse instructions
    instr_dict_path = parser.fetch_instr_dict()
    parser.parse_instructions(instr_dict_path)
    
    # Display results
    parser.print_summary_table()
    parser.print_multi_extension_instructions()


if __name__ == "__main__":
    main()
