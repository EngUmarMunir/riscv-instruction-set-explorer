"""
Tier 2: Cross-Reference and Comparison

This module compares extensions found in instr_dict.json against those
mentioned in the RISC-V ISA manual, handling naming normalization.
"""

from typing import Set, Dict, Tuple, List
from dataclasses import dataclass
from instruction_parser import InstructionParser
from manual_scanner import ManualScanner


@dataclass
class CrossReferenceReport:
    """Report of cross-reference analysis."""
    matched_extensions: Set[str]
    json_only: Set[str]
    manual_only: Set[str]
    
    def get_summary(self) -> str:
        """Get a formatted summary string."""
        return (
            f"{len(self.matched_extensions)} matched, "
            f"{len(self.json_only)} in JSON only, "
            f"{len(self.manual_only)} in manual only"
        )


class CrossReferencer:
    """Compares extensions between instr_dict.json and ISA manual."""
    
    def __init__(self, instruction_parser: InstructionParser, manual_scanner: ManualScanner):
        """
        Initialize cross-referencer.
        
        Args:
            instruction_parser: Initialized InstructionParser
            manual_scanner: Initialized ManualScanner
        """
        self.parser = instruction_parser
        self.scanner = manual_scanner
        self.report: CrossReferenceReport = None
    
    def normalize_extension_name(self, ext: str) -> str:
        """
        Normalize extension names for comparison.
        
        Handles:
        - Case insensitivity
        - rv_ prefix variants
        - Version numbers
        - Different capitalization
        
        Args:
            ext: Extension name to normalize
            
        Returns:
            Normalized extension name
        """
        return self.scanner._canonicalize_extension_name(ext)

    def _find_original_extension_key(self, normalized_ext: str) -> str:
        """Find the original extension key from instr_dict.json for a normalized name."""
        for original_ext in self.parser.get_extensions_dict().keys():
            if self.normalize_extension_name(original_ext) == normalized_ext:
                return original_ext
        return normalized_ext
    
    def cross_reference(self) -> CrossReferenceReport:
        """
        Perform cross-reference comparison.
        
        Returns:
            CrossReferenceReport with results
        """
        # Get extensions from both sources
        json_extensions = set(self.parser.get_extensions_dict().keys())
        manual_extensions = self.scanner.get_found_extensions()
        
        # Normalize both sets for comparison
        normalized_json = {self.normalize_extension_name(ext) for ext in json_extensions}
        normalized_manual = {self.normalize_extension_name(ext) for ext in manual_extensions}
        
        # Find matches, mismatches
        matched = normalized_json & normalized_manual
        json_only = normalized_json - normalized_manual
        manual_only = normalized_manual - normalized_json
        
        self.report = CrossReferenceReport(
            matched_extensions=matched,
            json_only=json_only,
            manual_only=manual_only
        )
        
        return self.report
    
    def print_report(self) -> None:
        """Print cross-reference report."""
        if not self.report:
            self.cross_reference()
        
        print("\n" + "="*80)
        print("CROSS-REFERENCE REPORT: instr_dict.json vs ISA Manual")
        print("="*80)
        
        print(f"\nSUMMARY: {self.report.get_summary()}")
        
        print("\n" + "-"*80)
        print("MATCHED EXTENSIONS (in both sources)")
        print("-"*80)
        if self.report.matched_extensions:
            for ext in sorted(self.report.matched_extensions):
                original_ext = self._find_original_extension_key(ext)
                json_count = len(self.parser.get_extensions_dict().get(original_ext, []))
                print(f"  ✓ {ext:<15} | {json_count} instruction(s) | [Original: {original_ext}]")
        else:
            print("  (None)")
        
        print("\n" + "-"*80)
        print("EXTENSIONS IN JSON ONLY (instr_dict.json)")
        print("-"*80)
        if self.report.json_only:
            for ext in sorted(self.report.json_only):
                original_ext = self._find_original_extension_key(ext)
                count = len(self.parser.get_extensions_dict().get(original_ext, []))
                print(f"  • {ext:<15} | {count} instruction(s) | [Original: {original_ext}]")
        else:
            print("  (None)")
        
        print("\n" + "-"*80)
        print("EXTENSIONS IN MANUAL ONLY (ISA Manual)")
        print("-"*80)
        if self.report.manual_only:
            for ext in sorted(self.report.manual_only):
                files = self.scanner.get_extension_files().get(ext, [])
                print(f"  • {ext:<15} | Found in {len(files)} file(s)")
        else:
            print("  (None)")
        
        print("\n" + "="*80)
        print("DETAILED STATISTICS")
        print("="*80)
        print(f"Total unique extensions in JSON:   {len(self.parser.get_extensions_dict())}")
        print(f"Total unique extensions in Manual: {len(self.scanner.get_found_extensions())}")
        print(f"Matched (normalized):              {len(self.report.matched_extensions)}")
        print(f"Match rate:                        "
              f"{(len(self.report.matched_extensions) / max(1, len(self.parser.get_extensions_dict())) * 100):.1f}%")
        print("="*80)
    
    def get_report(self) -> CrossReferenceReport:
        """Get the cross-reference report."""
        if not self.report:
            self.cross_reference()
        return self.report


def main():
    """Main entry point for cross-reference."""
    # Initialize parser
    parser = InstructionParser(data_dir="./data")
    instr_dict_path = parser.fetch_instr_dict()
    parser.parse_instructions(instr_dict_path)
    
    # Initialize scanner
    scanner = ManualScanner(data_dir="./data")
    scanner.clone_manual()
    scanner.scan_manual()
    
    # Perform cross-reference
    referencer = CrossReferencer(parser, scanner)
    referencer.cross_reference()
    referencer.print_report()


if __name__ == "__main__":
    main()
