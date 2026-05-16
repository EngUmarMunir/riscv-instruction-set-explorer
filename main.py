#!/usr/bin/env python3
"""
RISC-V Instruction Set Explorer - Main Entry Point

A comprehensive tool for analyzing RISC-V instruction sets across multiple tiers:

Tier 1: Parse instruction dictionaries and group by extension
Tier 2: Cross-reference with official RISC-V ISA manual
Tier 3: Generate visualizations and unit tests
"""

import sys
import argparse
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from instruction_parser import InstructionParser
from manual_scanner import ManualScanner
from cross_reference import CrossReferencer
from visualization import ExtensionGraph, GraphExporter


class RISCVExplorer:
    """Main orchestrator for the RISC-V exploration tasks."""
    
    def __init__(self, data_dir: str = "./data", verbose: bool = False):
        """
        Initialize the explorer.
        
        Args:
            data_dir: Directory for data storage
            verbose: Enable verbose output
        """
        self.data_dir = data_dir
        self.verbose = verbose
        self.parser = InstructionParser(data_dir=data_dir)
        self.scanner = ManualScanner(data_dir=data_dir)
        self.referencer = None
        self.graph = None
    
    def run_tier1(self, force_refresh: bool = False) -> None:
        """
        Run Tier 1: Instruction Set Parsing.
        
        Args:
            force_refresh: Force download of latest data
        """
        print("\n" + "="*80)
        print("TIER 1: INSTRUCTION SET PARSING")
        print("="*80)
        
        # Fetch instruction dictionary
        instr_dict_path = self.parser.fetch_instr_dict(force_refresh=force_refresh)
        
        # Parse instructions
        self.parser.parse_instructions(instr_dict_path)
        
        # Display results
        self.parser.print_summary_table()
        self.parser.print_multi_extension_instructions()
    
    def run_tier2(self, force_refresh: bool = False) -> None:
        """
        Run Tier 2: Cross-Reference with ISA Manual.
        
        Requires Tier 1 to be completed first.
        
        Args:
            force_refresh: Force re-clone of manual repo
        """
        if not self.parser.instructions:
            print("Tier 1 data not loaded yet; running Tier 1 first.")
            self.run_tier1(force_refresh=force_refresh)
        
        print("\n" + "="*80)
        print("TIER 2: CROSS-REFERENCE WITH ISA MANUAL")
        print("="*80)
        
        # Clone and scan manual
        self.scanner.clone_manual(force_refresh=force_refresh)
        self.scanner.scan_manual()
        self.scanner.print_found_extensions()
        
        # Perform cross-reference
        self.referencer = CrossReferencer(self.parser, self.scanner)
        self.referencer.cross_reference()
        self.referencer.print_report()
    
    def run_tier3(self) -> None:
        """
        Run Tier 3 Bonus: Visualization and Tests.
        
        Requires Tier 1 and Tier 2 to be completed first.
        """
        if not self.parser.instructions:
            print("Tier 1 data not loaded yet; running Tier 1 first.")
            self.run_tier1()
        
        print("\n" + "="*80)
        print("TIER 3 BONUS: VISUALIZATION")
        print("="*80)
        
        # Build graph
        self.graph = ExtensionGraph(self.parser)
        
        # Generate visualizations
        print(self.graph.generate_ascii_art_graph())
        print("\n")
        print(self.graph.generate_text_graph())
        
        # Export formats
        exporter = GraphExporter()
        data_path = Path(self.data_dir)
        data_path.mkdir(exist_ok=True)
        
        exporter.export_graphviz(self.graph, str(data_path / "extension_graph.dot"))
        exporter.export_adjacency_matrix(self.graph, str(data_path / "extension_adjacency.csv"))
        
        print("\n✓ Exported graph files to data directory")
    
    def run_all(self, force_refresh: bool = False) -> None:
        """
        Run all tiers in sequence.
        
        Args:
            force_refresh: Force refresh of all data sources
        """
        print("\n" + "="*80)
        print("RISC-V INSTRUCTION SET EXPLORER")
        print("Analyzing RISC-V Instructions and ISA Documentation")
        print("="*80)
        
        try:
            self.run_tier1(force_refresh=force_refresh)
            self.run_tier2(force_refresh=force_refresh)
            self.run_tier3()
            
            self._print_completion_summary()
        except Exception as e:
            print(f"\nERROR: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    def _print_completion_summary(self) -> None:
        """Print completion summary."""
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        
        if self.parser.instructions:
            print(f"✓ Parsed {len(self.parser.instructions)} instructions")
            print(f"✓ Grouped into {len(self.parser.get_extensions_dict())} extensions")
            print(f"✓ Identified {len(self.parser.get_multi_extension_instructions())} "
                  f"multi-extension instructions")
        
        if self.scanner.found_extensions:
            print(f"✓ Found {len(self.scanner.found_extensions)} extensions in ISA manual")
        
        if self.referencer:
            report = self.referencer.get_report()
            print(f"✓ Cross-reference: {report.get_summary()}")
        
        if self.graph:
            components = self.graph.get_connected_components()
            print(f"✓ Generated extension graph with {len(components)} connected components")
        
        print("\nOutput files saved in: ./data/")
        print("="*80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='RISC-V Instruction Set Explorer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tiers
  python main.py --all
  
  # Run only Tier 1
  python main.py --tier 1
  
  # Run Tiers 1 and 2
  python main.py --tier 1 --tier 2
  
  # Force refresh of all data
  python main.py --all --refresh
        """
    )
    
    parser.add_argument('--tier', type=int, choices=[1, 2, 3], action='append',
                       help='Run specific tier(s)')
    parser.add_argument('--all', action='store_true',
                       help='Run all tiers (default)')
    parser.add_argument('--refresh', action='store_true',
                       help='Force refresh of data sources')
    parser.add_argument('--data-dir', default='./data',
                       help='Directory for data storage (default: ./data)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Create explorer
    explorer = RISCVExplorer(data_dir=args.data_dir, verbose=args.verbose)
    
    # Determine which tiers to run
    if args.all or not args.tier:
        explorer.run_all(force_refresh=args.refresh)
    else:
        # Run specified tiers in order
        if 1 in args.tier:
            explorer.run_tier1(force_refresh=args.refresh)
        if 2 in args.tier:
            explorer.run_tier2(force_refresh=args.refresh)
        if 3 in args.tier:
            explorer.run_tier3()


if __name__ == "__main__":
    main()
