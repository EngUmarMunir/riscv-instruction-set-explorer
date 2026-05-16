"""
Tier 2: RISC-V ISA Manual Scanner

This module handles:
- Cloning/fetching the RISC-V ISA manual repository
- Scanning AsciiDoc source files for extension references
- Extracting extension names from documentation
"""

import re
import subprocess
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set


class ManualScanner:
    """Scanner for RISC-V ISA manual documentation."""
    
    MANUAL_REPO_URL = "https://github.com/riscv/riscv-isa-manual.git"
    MANUAL_DIR = "riscv-isa-manual"

    # Manual-specific extension markers that should be treated as authoritative.
    EXTENSION_MARKER_PATTERNS = (
        re.compile(r'\bext(?:link)?:([A-Za-z][A-Za-z0-9_]*)\[\]', re.IGNORECASE),
        re.compile(r'\[\[ext:([A-Za-z][A-Za-z0-9_]*)\]\]', re.IGNORECASE),
    )
    
    # Standard RISC-V extension names to look for
    KNOWN_EXTENSIONS = {
        'i', 'm', 'a', 'f', 'd', 'q', 'c',  # Base and standard
        'zicsr', 'zifencei', 'zihintpause',  # Privileged
        'zba', 'zbb', 'zbc', 'zbs',  # Bitmanip
        'zfh', 'zfinx', 'zdinx', 'zhinx', 'zhinxmin',  # Float variants
        'zmmul', 'zksed', 'zksh', 'zk', 'zkn', 'zkr', 'zks', 'zkt',  # Crypto
        'zve32x', 'zve32f', 'zve64x', 'zve64f', 'zve64d',  # Vector
        'zvl32b', 'zvl64b', 'zvl128b', 'zvl256b', 'zvl512b', 'zvl1024b',
        'v',  # Full vector
        'zpn', 'zpsf',  # DSP extensions
        'sm',  # Supervisor mode
        's',  # Supervisor
        'u',  # User
        'h',  # Hypervisor
    }
    
    def __init__(self, data_dir: str = "./data"):
        """
        Initialize the manual scanner.
        
        Args:
            data_dir: Directory to store cloned manual
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.manual_path = self.data_dir / self.MANUAL_DIR
        self.found_extensions: Set[str] = set()
        self.extension_files: Dict[str, List[str]] = defaultdict(list)

    def _canonicalize_extension_name(self, ext: str) -> str:
        """Normalize an extension name to a comparison key."""
        value = str(ext or '').strip().lower()
        value = value.strip('`[](),.:;')
        value = re.sub(r'^(?:extlink|ext):', '', value)
        value = re.sub(r'^rv(?:\d+)?_?', '', value)
        value = re.sub(r'^rv\d+', '', value)

        match = re.match(r'^(.*?)(\d+)$', value)
        if match:
            stem = match.group(1)
            if stem in self.KNOWN_EXTENSIONS or re.match(r'^(?:[abcdfhimqsuvxz]|za|zb|zc|zd|ze|zf|zg|zh|zi|zk|zl|zm|zn|zp|zv|ss|sm|sv)[a-z0-9_]*$', stem):
                value = stem
        return value

    def _record_extension(self, ext: str, source_file: str, seen_in_file: Set[str]) -> None:
        normalized = self._canonicalize_extension_name(ext)
        if not normalized or not self._is_valid_extension(normalized):
            return
        if normalized in seen_in_file:
            return

        seen_in_file.add(normalized)
        self.found_extensions.add(normalized)
        self.extension_files[normalized].append(source_file)
    
    def clone_manual(self, force_refresh: bool = False) -> str:
        """
        Clone the RISC-V ISA manual repository.
        
        Args:
            force_refresh: If True, re-clone even if already present
            
        Returns:
            Path to the cloned repository
        """
        if self.manual_path.exists():
            if not force_refresh:
                print(f"Manual repository already exists at {self.manual_path}")
                return str(self.manual_path)

            print(f"Refreshing manual repository at {self.manual_path}...")
            shutil.rmtree(self.manual_path)
        
        try:
            print(f"Cloning RISC-V ISA manual from {self.MANUAL_REPO_URL}...")
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', self.MANUAL_REPO_URL, str(self.manual_path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            print(f"Repository cloned successfully to {self.manual_path}")
            return str(self.manual_path)
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e.stderr}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise
    
    def update_manual(self) -> None:
        """Update the cloned manual repository."""
        if not self.manual_path.exists():
            self.clone_manual()
            return
        
        try:
            print(f"Updating RISC-V ISA manual...")
            result = subprocess.run(
                ['git', 'pull'],
                cwd=str(self.manual_path),
                check=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            print("Repository updated successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error updating repository: {e.stderr}")
        except Exception as e:
            print(f"Unexpected error: {e}")
    
    def scan_manual(self) -> None:
        """Scan the manual for extension references."""
        if not self.manual_path.exists():
            print("Manual not found, cloning...")
            self.clone_manual()
        
        print(f"Scanning manual directory: {self.manual_path / 'src'}")
        
        src_dir = self.manual_path / 'src'
        if not src_dir.exists():
            print(f"Source directory not found at {src_dir}")
            return
        
        adoc_files = list(src_dir.rglob('*.adoc'))
        print(f"Found {len(adoc_files)} AsciiDoc files")
        
        for adoc_file in adoc_files:
            try:
                with open(adoc_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    self._extract_extensions_from_content(content, str(adoc_file))
            except Exception as e:
                print(f"Error reading {adoc_file}: {e}")
    
    def _extract_extensions_from_content(self, content: str, source_file: str) -> None:
        """
        Extract extension references from document content.
        
        Args:
            content: Document content to scan
            source_file: Source file path for tracking
        """
        seen_in_file: Set[str] = set()

        # Prefer the manual's own extension markers.
        for pattern in self.EXTENSION_MARKER_PATTERNS:
            for match in pattern.finditer(content):
                self._record_extension(match.group(1), source_file, seen_in_file)

        # Fallback for explicit prose mentions in the manual and tests.
        for ext in self.KNOWN_EXTENSIONS:
            patterns = [
                rf'\b{re.escape(ext.upper())}\b',
                rf'\b{re.escape(ext)}\b',
                rf'\brv_{re.escape(ext)}\b',
                rf'\b{re.escape(ext)}\s+extension\b',
            ]

            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    self._record_extension(ext, source_file, seen_in_file)
                    break
    
    def _normalize_extension_name(self, ext: str) -> str:
        """
        Normalize extension names to a standard format.
        
        Handles various naming conventions:
        - rv_zba -> zba
        - Zba -> zba
        - RV64I -> i (extracts base extension)
        
        Args:
            ext: Extension name to normalize
            
        Returns:
            Normalized extension name
        """
        return self._canonicalize_extension_name(ext)
    
    def _is_valid_extension(self, ext: str) -> bool:
        """
        Check if a string looks like a valid extension name.
        
        Args:
            ext: String to check
            
        Returns:
            True if it looks like an extension name
        """
        # Must be at least 1 character
        if not ext or len(ext) > 32:
            return False
        
        # Should contain only alphanumeric and underscores
        if not re.match(r'^[a-z][a-z0-9_]*$', ext):
            return False
        
        # Should not be a common word
        common_words = {'the', 'and', 'for', 'with', 'from', 'instruction',
                       'register', 'memory', 'extension', 'format', 'mode'}
        if ext in common_words:
            return False
        
        return True
    
    def get_found_extensions(self) -> Set[str]:
        """Return set of found extensions."""
        return self.found_extensions
    
    def get_extension_files(self) -> Dict[str, List[str]]:
        """Return mapping of extensions to source files."""
        return dict(self.extension_files)
    
    def print_found_extensions(self) -> None:
        """Print found extensions."""
        print("\n" + "="*70)
        print("EXTENSIONS FOUND IN ISA MANUAL")
        print("="*70)
        for ext in sorted(self.found_extensions):
            files = self.extension_files[ext]
            print(f"{ext:<20} | Found in {len(files)} file(s)")
        print("="*70)


def main():
    """Main entry point for manual scanner."""
    scanner = ManualScanner(data_dir="./data")
    scanner.clone_manual()
    scanner.scan_manual()
    scanner.print_found_extensions()


if __name__ == "__main__":
    main()
