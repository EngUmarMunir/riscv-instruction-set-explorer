"""
Tier 3 Bonus: Comprehensive Unit Tests

Tests for all three tiers of the RISC-V Instruction Set Explorer.
"""

import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from instruction_parser import InstructionParser, Instruction
from manual_scanner import ManualScanner
from cross_reference import CrossReferencer, CrossReferenceReport
from visualization import ExtensionGraph, GraphExporter


class TestInstructionParser(unittest.TestCase):
    """Tests for Tier 1: Instruction Set Parsing"""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.parser = InstructionParser(data_dir=self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def _create_test_instr_dict(self, data: dict) -> str:
        """Helper to create a test instruction dictionary."""
        path = Path(self.test_dir) / "test_instr.json"
        with open(path, 'w') as f:
            json.dump(data, f)
        return str(path)
    
    def test_parse_simple_instructions(self):
        """Test parsing simple instruction set."""
        test_data = [
            {
                "name": "ADD",
                "extensions": ["i"],
                "description": "Add two registers"
            },
            {
                "name": "MUL",
                "extensions": ["m"],
                "description": "Multiply two registers"
            }
        ]
        
        instr_file = self._create_test_instr_dict(test_data)
        self.parser.parse_instructions(instr_file)
        
        self.assertEqual(len(self.parser.instructions), 2)
        self.assertIn("ADD", self.parser.instructions)
        self.assertIn("MUL", self.parser.instructions)
    
    def test_multi_extension_instructions(self):
        """Test identifying instructions with multiple extensions."""
        test_data = [
            {
                "name": "SH1ADD",
                "extensions": ["zba", "i"],
                "description": "Shift and add"
            },
            {
                "name": "ADD",
                "extensions": ["i"],
                "description": "Add"
            }
        ]
        
        instr_file = self._create_test_instr_dict(test_data)
        self.parser.parse_instructions(instr_file)
        
        multi_ext = self.parser.get_multi_extension_instructions()
        self.assertEqual(len(multi_ext), 1)
        self.assertEqual(multi_ext[0][0], "SH1ADD")
        self.assertEqual(len(multi_ext[0][1]), 2)
    
    def test_extension_grouping(self):
        """Test that extensions are properly grouped."""
        test_data = [
            {"name": "ADD", "extensions": ["i"]},
            {"name": "ADDI", "extensions": ["i"]},
            {"name": "MUL", "extensions": ["m"]},
        ]
        
        instr_file = self._create_test_instr_dict(test_data)
        self.parser.parse_instructions(instr_file)
        
        ext_dict = self.parser.get_extensions_dict()
        self.assertEqual(len(ext_dict["i"]), 2)
        self.assertEqual(len(ext_dict["m"]), 1)
    
    def test_case_normalization(self):
        """Test that extension names are normalized to lowercase."""
        test_data = [
            {"name": "ADD", "extensions": ["I"]},
            {"name": "MUL", "extensions": ["M"]},
        ]
        
        instr_file = self._create_test_instr_dict(test_data)
        self.parser.parse_instructions(instr_file)
        
        ext_dict = self.parser.get_extensions_dict()
        self.assertIn("i", ext_dict)
        self.assertIn("m", ext_dict)
        self.assertNotIn("I", ext_dict)
        self.assertNotIn("M", ext_dict)
    
    def test_get_extension_summary(self):
        """Test generation of extension summary."""
        test_data = [
            {"name": "ADD", "extensions": ["i"]},
            {"name": "MUL", "extensions": ["i"]},
            {"name": "MULH", "extensions": ["m"]},
        ]
        
        instr_file = self._create_test_instr_dict(test_data)
        self.parser.parse_instructions(instr_file)
        
        summary = self.parser.get_extension_summary()
        # Should have 2 extensions
        self.assertEqual(len(summary), 2)
        
        # Check format: (ext_name, count, example)
        for ext_name, count, example in summary:
            self.assertIsInstance(ext_name, str)
            self.assertIsInstance(count, int)
            self.assertIsInstance(example, str)
            self.assertGreater(count, 0)


class TestManualScanner(unittest.TestCase):
    """Tests for Tier 2: Manual Scanning"""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.scanner = ManualScanner(data_dir=self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_normalize_extension_name(self):
        """Test extension name normalization."""
        test_cases = [
            ("rv_zba", "zba"),
            ("ZBA", "zba"),
            ("Zba", "zba"),
            ("rv_i", "i"),
            ("RV64I", "i"),
            ("zba1", "zba"),
            ("ext:zicsr[]", "zicsr"),
            ("extlink:zifencei[]", "zifencei"),
        ]
        
        for input_name, expected in test_cases:
            result = self.scanner._normalize_extension_name(input_name)
            self.assertEqual(result, expected, 
                           f"Failed for {input_name}: got {result}, expected {expected}")
    
    def test_is_valid_extension(self):
        """Test extension name validation."""
        valid = ["zba", "i", "m", "zicsr", "zfinx"]
        invalid = ["the", "and", "instruction", "123_bad", ""]
        
        for ext in valid:
            self.assertTrue(self.scanner._is_valid_extension(ext),
                          f"{ext} should be valid")
        
        for ext in invalid:
            self.assertFalse(self.scanner._is_valid_extension(ext),
                           f"{ext} should be invalid")
    
    def test_extension_extraction_from_content(self):
        """Test extracting extensions from document content."""
        content = """
        The Zba extension provides shift-add instructions.
        The rv_i extension is the base integer ISA.
        Vector extension (V) offers SIMD capabilities.
        """
        
        self.scanner._extract_extensions_from_content(content, "test.adoc")
        found = self.scanner.get_found_extensions()
        
        # Check that some known extensions were found
        # The exact extensions found depend on KNOWN_EXTENSIONS set
        self.assertGreater(len(found), 0)

    def test_extension_extraction_from_manual_markers(self):
        """Test extracting extensions from the ISA manual's own ext markers."""
        content = """
        [[ext:zba]]
        === ext:zba[] Extension for Address Generation

        The extlink:zicsr[] extension is required.
        The ext:svvptc[] extension updates PTE validity.
        """

        self.scanner._extract_extensions_from_content(content, "manual.adoc")
        found = self.scanner.get_found_extensions()

        self.assertIn("zba", found)
        self.assertIn("zicsr", found)
        self.assertIn("svvptc", found)


class TestCrossReference(unittest.TestCase):
    """Tests for Tier 2: Cross-Reference"""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create test instruction data
        test_data = [
            {"name": "ADD", "extensions": ["i"]},
            {"name": "MUL", "extensions": ["m"]},
            {"name": "ADDEXT", "extensions": ["ext1"]},
        ]
        
        path = Path(self.test_dir) / "test_instr.json"
        with open(path, 'w') as f:
            json.dump(test_data, f)
        
        self.parser = InstructionParser(data_dir=self.test_dir)
        self.parser.parse_instructions(str(path))
        
        self.scanner = ManualScanner(data_dir=self.test_dir)
        self.scanner.found_extensions = {"i", "m"}  # Simulate manual findings
        
        self.referencer = CrossReferencer(self.parser, self.scanner)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_normalize_extension_name(self):
        """Test extension normalization in cross-referencer."""
        test_cases = [
            ("rv_zba", "zba"),
            ("ZBA", "zba"),
            ("zba1", "zba"),
            ("RV64I", "i"),
            ("ext:zicsr[]", "zicsr"),
        ]
        
        for input_name, expected in test_cases:
            result = self.referencer.normalize_extension_name(input_name)
            self.assertEqual(result, expected)
    
    def test_cross_reference_matching(self):
        """Test cross-reference finds matches."""
        report = self.referencer.cross_reference()
        
        # "i" and "m" are in both JSON and manual
        self.assertIn("i", report.matched_extensions)
        self.assertIn("m", report.matched_extensions)
        
        # "ext1" is only in JSON
        self.assertIn("ext1", report.json_only)
    
    def test_report_summary(self):
        """Test cross-reference report summary generation."""
        report = self.referencer.cross_reference()
        summary = report.get_summary()
        
        self.assertIn("matched", summary)
        self.assertIn("in JSON only", summary)
        self.assertIn("in manual only", summary)


class TestExtensionGraph(unittest.TestCase):
    """Tests for Tier 3: Visualization"""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create test data with shared instructions
        test_data = [
            {"name": "ADD", "extensions": ["i"]},
            {"name": "SHARED1", "extensions": ["i", "m"]},
            {"name": "SHARED2", "extensions": ["m", "zba"]},
            {"name": "MUL", "extensions": ["m"]},
            {"name": "ZLONE", "extensions": ["zba"]},
        ]
        
        path = Path(self.test_dir) / "test_instr.json"
        with open(path, 'w') as f:
            json.dump(test_data, f)
        
        self.parser = InstructionParser(data_dir=self.test_dir)
        self.parser.parse_instructions(str(path))
        
        self.graph = ExtensionGraph(self.parser)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_graph_adjacency_list(self):
        """Test that adjacency list is correctly built."""
        adjacency = self.graph.get_adjacency_list()
        
        # "i" and "m" share an instruction, so should be connected
        self.assertIn("m", adjacency.get("i", set()))
        self.assertIn("i", adjacency.get("m", set()))
        
        # "m" and "zba" share an instruction
        self.assertIn("zba", adjacency.get("m", set()))
        self.assertIn("m", adjacency.get("zba", set()))
    
    def test_shared_instructions_tracking(self):
        """Test that shared instructions are tracked correctly."""
        shared = self.graph.get_shared_instructions()
        
        # Find the connection between i and m
        pair = tuple(sorted(["i", "m"]))
        self.assertIn(pair, shared)
        self.assertIn("SHARED1", shared[pair])
    
    def test_connected_components(self):
        """Test finding connected components in the graph."""
        components = self.graph.get_connected_components()
        
        # Should have at least one component with i, m, zba all connected
        self.assertGreater(len(components), 0)
        
        # The largest component should have multiple extensions
        self.assertGreater(len(components[0]), 1)
    
    def test_graph_generation(self):
        """Test that graph generation methods work."""
        text_graph = self.graph.generate_text_graph()
        self.assertIsInstance(text_graph, str)
        self.assertIn("EXTENSION RELATIONSHIP GRAPH", text_graph)
        
        ascii_art = self.graph.generate_ascii_art_graph()
        self.assertIsInstance(ascii_art, str)
        self.assertIn("EXTENSION NETWORK VISUALIZATION", ascii_art)
        
        dot = self.graph.generate_graphviz_dot()
        self.assertIsInstance(dot, str)
        self.assertIn("graph extension_graph", dot)


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple tiers."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create comprehensive test data
        test_data = [
            {"name": "ADD", "extensions": ["i"]},
            {"name": "ADDI", "extensions": ["i"]},
            {"name": "MUL", "extensions": ["m"]},
            {"name": "MULH", "extensions": ["m"]},
            {"name": "SH1ADD", "extensions": ["zba", "i"]},
            {"name": "SH2ADD", "extensions": ["zba", "m"]},
            {"name": "AND", "extensions": ["i", "b"]},
        ]
        
        path = Path(self.test_dir) / "test_instr.json"
        with open(path, 'w') as f:
            json.dump(test_data, f)
        
        self.parser = InstructionParser(data_dir=self.test_dir)
        self.parser.parse_instructions(str(path))
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_end_to_end_parsing_and_grouping(self):
        """Test complete flow from parsing to summary."""
        summary = self.parser.get_extension_summary()
        
        # Should have parsed all extensions
        self.assertGreater(len(summary), 0)
        
        # All summaries should have correct format
        for ext_name, count, example in summary:
            self.assertIsInstance(ext_name, str)
            self.assertIsInstance(count, int)
            self.assertIsInstance(example, str)
            self.assertGreater(count, 0)
    
    def test_multi_extension_handling(self):
        """Test proper handling of multi-extension instructions."""
        multi = self.parser.get_multi_extension_instructions()
        
        # Should find SH1ADD, SH2ADD, AND with multiple extensions
        self.assertGreater(len(multi), 0)
        
        instr_names = [name for name, _ in multi]
        self.assertIn("SH1ADD", instr_names)
        self.assertIn("SH2ADD", instr_names)
        self.assertIn("AND", instr_names)
    
    def test_graph_from_parsed_data(self):
        """Test graph generation from parsed instruction data."""
        graph = ExtensionGraph(self.parser)
        
        # Extensions that share instructions should be connected
        adjacency = graph.get_adjacency_list()
        
        # i and zba share SH1ADD
        self.assertIn("zba", adjacency.get("i", set()))
        
        # m and zba share SH2ADD
        self.assertIn("zba", adjacency.get("m", set()))


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
