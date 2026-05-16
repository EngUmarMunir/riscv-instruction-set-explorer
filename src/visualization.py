"""
Tier 3 Bonus: Extension Relationship Visualization

This module generates graphs showing which extensions share instructions.
Extensions are connected if they share at least one instruction.
"""

from typing import Dict, List, Set, Tuple
from collections import defaultdict
from instruction_parser import InstructionParser


class ExtensionGraph:
    """Graph representing relationships between extensions based on shared instructions."""
    
    def __init__(self, instruction_parser: InstructionParser):
        """
        Initialize extension graph.
        
        Args:
            instruction_parser: Initialized InstructionParser
        """
        self.parser = instruction_parser
        self.adjacency_list: Dict[str, Set[str]] = defaultdict(set)
        self.shared_instructions: Dict[Tuple[str, str], Set[str]] = defaultdict(set)
        self._build_graph()
    
    def _build_graph(self) -> None:
        """Build the extension relationship graph."""
        # For each instruction with multiple extensions, connect those extensions
        multi_ext_instrs = self.parser.get_multi_extension_instructions()
        
        for instr_name, extensions in multi_ext_instrs:
            # Connect all pairs of extensions that share this instruction
            for i in range(len(extensions)):
                for j in range(i + 1, len(extensions)):
                    ext1, ext2 = extensions[i], extensions[j]
                    # Add bidirectional edges
                    self.adjacency_list[ext1].add(ext2)
                    self.adjacency_list[ext2].add(ext1)
                    
                    # Track shared instructions (sorted pair for consistency)
                    pair = tuple(sorted([ext1, ext2]))
                    self.shared_instructions[pair].add(instr_name)
    
    def get_adjacency_list(self) -> Dict[str, Set[str]]:
        """Get the adjacency list representation."""
        return dict(self.adjacency_list)
    
    def get_shared_instructions(self) -> Dict[Tuple[str, str], Set[str]]:
        """Get mapping of extension pairs to shared instructions."""
        return dict(self.shared_instructions)
    
    def get_connected_components(self) -> List[Set[str]]:
        """
        Find connected components in the graph.
        
        Returns:
            List of sets, each containing connected extensions
        """
        visited = set()
        components = []
        
        def dfs(node: str, component: Set[str]) -> None:
            visited.add(node)
            component.add(node)
            for neighbor in self.adjacency_list[node]:
                if neighbor not in visited:
                    dfs(neighbor, component)
        
        all_extensions = set(self.adjacency_list.keys())
        for ext in all_extensions:
            if ext not in visited:
                component = set()
                dfs(ext, component)
                components.append(component)
        
        return sorted(components, key=len, reverse=True)
    
    def generate_text_graph(self) -> str:
        """
        Generate a text-based representation of the graph.
        
        Returns:
            Formatted string representing the graph
        """
        output = []
        output.append("="*80)
        output.append("EXTENSION RELATIONSHIP GRAPH")
        output.append("(Extensions connected if they share at least one instruction)")
        output.append("="*80)
        
        # Sort extensions for consistent output
        for ext in sorted(self.adjacency_list.keys()):
            neighbors = sorted(self.adjacency_list[ext])
            if neighbors:
                for neighbor in neighbors:
                    # Only print each edge once (when ext < neighbor alphabetically)
                    if ext < neighbor:
                        pair = tuple(sorted([ext, neighbor]))
                        shared = self.shared_instructions[pair]
                        output.append(f"\n{ext} ←→ {neighbor}")
                        output.append(f"  Shared instructions: {', '.join(sorted(shared))}")
        
        output.append("\n" + "="*80)
        return "\n".join(output)
    
    def generate_graphviz_dot(self) -> str:
        """
        Generate Graphviz DOT format for the graph.
        
        Returns:
            DOT format string
        """
        lines = []
        lines.append("graph extension_graph {")
        lines.append('  node [shape=box, style=rounded];')
        lines.append("  rankdir=LR;")
        
        # Add nodes
        for ext in sorted(self.adjacency_list.keys()):
            # Color based on number of connections
            neighbors_count = len(self.adjacency_list[ext])
            color = self._get_color_by_connectivity(neighbors_count)
            lines.append(f'  "{ext}" [fillcolor="{color}", style="rounded,filled"];')
        
        # Add edges
        added_edges = set()
        for ext in sorted(self.adjacency_list.keys()):
            for neighbor in sorted(self.adjacency_list[ext]):
                # Only add each edge once
                edge = tuple(sorted([ext, neighbor]))
                if edge not in added_edges:
                    pair = tuple(sorted([ext, neighbor]))
                    shared_count = len(self.shared_instructions[pair])
                    label = f"{shared_count} instruction{'s' if shared_count != 1 else ''}"
                    lines.append(f'  "{ext}" -- "{neighbor}" [label="{label}"];')
                    added_edges.add(edge)
        
        lines.append("}")
        return "\n".join(lines)
    
    def _get_color_by_connectivity(self, neighbor_count: int) -> str:
        """Get color based on connectivity."""
        if neighbor_count == 0:
            return "lightgray"
        elif neighbor_count == 1:
            return "lightgreen"
        elif neighbor_count <= 3:
            return "lightyellow"
        elif neighbor_count <= 6:
            return "lightblue"
        else:
            return "lightcoral"
    
    def generate_ascii_art_graph(self) -> str:
        """
        Generate ASCII art representation of the graph.
        
        Returns:
            ASCII art representation
        """
        output = []
        output.append("="*80)
        output.append("EXTENSION NETWORK VISUALIZATION")
        output.append("="*80)
        
        components = self.get_connected_components()
        
        for i, component in enumerate(components):
            output.append(f"\nConnected Component {i+1} ({len(component)} extensions):")
            output.append("-" * 40)
            
            for ext in sorted(component):
                neighbors = sorted(self.adjacency_list[ext])
                if neighbors:
                    neighbor_str = ", ".join(neighbors)
                    output.append(f"  {ext:15} → {neighbor_str}")
        
        # Summary statistics
        output.append("\n" + "="*80)
        output.append("GRAPH STATISTICS")
        output.append("="*80)
        
        all_edges = 0
        for ext in self.adjacency_list:
            all_edges += len(self.adjacency_list[ext])
        all_edges //= 2  # Each edge counted twice
        
        isolated = len(self.parser.get_extensions_dict()) - len(self.adjacency_list)
        
        output.append(f"Total extensions in instruction set: {len(self.parser.get_extensions_dict())}")
        output.append(f"Extensions sharing instructions:    {len(self.adjacency_list)}")
        output.append(f"Isolated extensions:                {isolated}")
        output.append(f"Total connections (edges):          {all_edges}")
        output.append(f"Connected components:               {len(components)}")
        output.append(f"Largest component size:             {len(components[0]) if components else 0}")
        output.append("="*80)
        
        return "\n".join(output)


class GraphExporter:
    """Export extension graphs in various formats."""
    
    @staticmethod
    def export_graphviz(graph: ExtensionGraph, output_path: str) -> None:
        """
        Export graph to Graphviz DOT format.
        
        Args:
            graph: ExtensionGraph to export
            output_path: Path to save DOT file
        """
        dot_content = graph.generate_graphviz_dot()
        with open(output_path, 'w') as f:
            f.write(dot_content)
        print(f"Exported Graphviz DOT to {output_path}")
    
    @staticmethod
    def export_adjacency_matrix(graph: ExtensionGraph, output_path: str) -> None:
        """
        Export graph as adjacency matrix (CSV format).
        
        Args:
            graph: ExtensionGraph to export
            output_path: Path to save CSV file
        """
        adjacency = graph.get_adjacency_list()
        extensions = sorted(adjacency.keys())
        
        lines = []
        # Header
        lines.append("," + ",".join(extensions))
        
        # Matrix rows
        for ext1 in extensions:
            row = [ext1]
            for ext2 in extensions:
                if ext2 in adjacency.get(ext1, set()):
                    row.append("1")
                else:
                    row.append("0")
            lines.append(",".join(row))
        
        with open(output_path, 'w') as f:
            f.write("\n".join(lines))
        print(f"Exported adjacency matrix to {output_path}")


def main():
    """Main entry point for graph generation."""
    # Initialize parser
    parser = InstructionParser(data_dir="./data")
    instr_dict_path = parser.fetch_instr_dict()
    parser.parse_instructions(instr_dict_path)
    
    # Build graph
    graph = ExtensionGraph(parser)
    
    # Generate and print visualizations
    print(graph.generate_ascii_art_graph())
    print("\n")
    print(graph.generate_text_graph())
    
    # Export formats
    exporter = GraphExporter()
    exporter.export_graphviz(graph, "./data/extension_graph.dot")
    exporter.export_adjacency_matrix(graph, "./data/extension_adjacency.csv")


if __name__ == "__main__":
    main()
