#!/usr/bin/env python3
"""
Generate visualization graphs from semantic doc relations.

Creates:
1. Per-folder subgraphs (e.g., doc/backend/layer-2-workflow-orchestration/)
2. Layer-level graphs (e.g., all docs in backend/)
3. Master graph (all docs across doc/)

Output: GraphViz DOT files + rendered SVG/PNG
"""

import os
import sys
import re
import yaml
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Set

class DocGraph:
    def __init__(self, doc_root: Path = None):
        self.doc_root = doc_root or Path("doc")
        self.docs: Dict[str, Dict] = {}  # path -> metadata
        self.folders: Dict[str, List[str]] = defaultdict(list)  # folder -> doc_paths
        self.relations: List[Tuple[str, str, str]] = []  # (source, target, type)
        
    def scan_docs(self):
        """Scan all .md files and extract YAML headers."""
        for md_file in self.doc_root.rglob("*.md"):
            if self._should_ignore(md_file):
                continue
            
            rel_path = md_file.relative_to(self.doc_root)
            folder = str(rel_path.parent)
            doc_id = rel_path.stem  # filename without .md
            
            # Parse YAML header
            header = self._parse_yaml_header(md_file)
            if not header:
                continue
            
            self.docs[doc_id] = {
                "path": str(rel_path),
                "file": md_file,
                "folder": folder,
                "title": header.get("title", doc_id),
                "semantic_blocks": header.get("semantic_blocks", []),
                "relations": header.get("relations", []),
            }
            
            self.folders[folder].append(doc_id)
            
            # Extract relations
            for rel in header.get("relations", []):
                self._add_relation(doc_id, rel)
    
    def _should_ignore(self, path: Path) -> bool:
        """Skip certain files."""
        name = path.name.lower()
        ignore = {"readme.md", "index.md", ".git"}
        return name in ignore
    
    def _parse_yaml_header(self, md_file: Path) -> Dict:
        """Extract YAML frontmatter from markdown file."""
        try:
            content = md_file.read_text()
            if not content.startswith("---"):
                return {}
            
            # Find closing ---
            lines = content.split("\n")
            end_idx = None
            for i, line in enumerate(lines[1:], start=1):
                if line.strip() == "---":
                    end_idx = i
                    break
            
            if end_idx is None:
                return {}
            
            yaml_content = "\n".join(lines[1:end_idx])
            return yaml.safe_load(yaml_content) or {}
        except Exception as e:
            print(f"⚠️  Error parsing {md_file}: {e}", file=sys.stderr)
            return {}
    
    def _add_relation(self, source_id: str, relation: Dict):
        """Add a relation edge to the graph."""
        target = relation.get("target", "")
        rel_type = relation.get("type", "references")
        
        # Resolve target ID
        target_id = self._resolve_target(target, source_id)
        if target_id and target_id in self.docs:
            self.relations.append((source_id, target_id, rel_type))
    
    def _resolve_target(self, target: str, source_id: str) -> str:
        """Resolve target filename/ID to doc_id."""
        # Remove .md and path components
        target = target.replace(".md", "").split("/")[-1]
        return target
    
    def generate_folder_graphs(self, output_dir: Path = None):
        """Generate one graph per folder."""
        output_dir = output_dir or Path("doc/.graphs")
        output_dir.mkdir(exist_ok=True)
        
        for folder, doc_ids in sorted(self.folders.items()):
            if not doc_ids:
                continue
            
            dot_content = self._generate_dot(
                folder=folder,
                node_ids=set(doc_ids)
            )
            
            # Clean folder name for filename
            folder_name = folder.replace("/", "_").replace(".", "")
            if not folder_name:
                folder_name = "root"
            
            dot_file = output_dir / f"{folder_name}.dot"
            dot_file.write_text(dot_content)
            
            svg_file = output_dir / f"{folder_name}.svg"
            print(f"📊 {folder}: {dot_file} (graph with {len(doc_ids)} docs, {self._count_edges(doc_ids)} relations)")
            
            # Generate SVG if graphviz available
            try:
                os.system(f"dot -Tsvg {dot_file} -o {svg_file} 2>/dev/null")
                if svg_file.exists():
                    print(f"   → {svg_file} ✅")
            except:
                pass
    
    def generate_master_graph(self, output_dir: Path = None):
        """Generate master graph of all docs."""
        output_dir = output_dir or Path("doc/.graphs")
        output_dir.mkdir(exist_ok=True)
        
        dot_content = self._generate_dot(
            folder="All Documentation",
            node_ids=set(self.docs.keys())
        )
        
        dot_file = output_dir / "master.dot"
        dot_file.write_text(dot_content)
        
        svg_file = output_dir / "master.svg"
        print(f"\n🌍 Master Graph: {len(self.docs)} docs, {len(self.relations)} relations")
        print(f"   {dot_file}")
        
        try:
            os.system(f"dot -Tsvg {dot_file} -o {svg_file} 2>/dev/null")
            if svg_file.exists():
                print(f"   → {svg_file} ✅")
        except:
            pass
    
    def _generate_dot(self, folder: str, node_ids: Set[str]) -> str:
        """Generate GraphViz DOT format for a subgraph."""
        lines = [
            'digraph "Doc Graph" {',
            '  rankdir=LR;',
            '  node [shape=box, style=rounded];',
            f'  label="{folder}";',
            '  ',
        ]
        
        # Nodes
        for doc_id in sorted(node_ids):
            if doc_id not in self.docs:
                continue
            title = self.docs[doc_id]["title"][:30]
            lines.append(f'  "{doc_id}" [label="{title}"];')
        
        lines.append("  ")
        
        # Edges (only within this subgraph)
        edge_colors = {
            "depends-on": "#e74c3c",      # red
            "part-of": "#3498db",         # blue
            "composed-of": "#2ecc71",     # green
            "implements": "#f39c12",      # orange
            "extends": "#9b59b6",         # purple
            "references": "#95a5a6",      # gray
            "deprecates": "#c0392b",      # dark red
        }
        
        for source, target, rel_type in self.relations:
            if source in node_ids and target in node_ids:
                color = edge_colors.get(rel_type, "#95a5a6")
                lines.append(f'  "{source}" -> "{target}" [label="{rel_type}", color="{color}"];')
        
        lines.extend([
            "}",
            "",
        ])
        
        return "\n".join(lines)
    
    def _count_edges(self, node_ids: Set[str]) -> int:
        """Count relations within a set of nodes."""
        return sum(1 for s, t, _ in self.relations if s in node_ids and t in node_ids)
    
    def generate_readme_section(self, folder: str) -> str:
        """Generate README section listing docs in a folder."""
        doc_ids = self.folders.get(folder, [])
        if not doc_ids:
            return ""
        
        lines = [
            f"## {folder}",
            "",
            "| Doc | Purpose | Status |",
            "|-----|---------|--------|",
        ]
        
        for doc_id in sorted(doc_ids):
            doc = self.docs[doc_id]
            title = doc["title"]
            status = doc.get("status", "unknown")
            lines.append(f"| {doc_id} | {title} | {status} |")
        
        lines.append("")
        return "\n".join(lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate doc relation graphs")
    parser.add_argument("--doc-root", type=Path, default=Path("doc"), help="Doc root folder")
    parser.add_argument("--output", type=Path, default=Path("doc/.graphs"), help="Output folder")
    parser.add_argument("--master-only", action="store_true", help="Only generate master graph")
    parser.add_argument("--folder-only", action="store_true", help="Only generate folder graphs")
    parser.add_argument("--readme", action="store_true", help="Generate README sections")
    
    args = parser.parse_args()
    
    # Scan
    print(f"📂 Scanning {args.doc_root}...")
    graph = DocGraph(args.doc_root)
    graph.scan_docs()
    
    print(f"✅ Found {len(graph.docs)} docs, {len(graph.relations)} relations")
    print()
    
    # Generate graphs
    if not args.master_only:
        graph.generate_folder_graphs(args.output)
    
    if not args.folder_only:
        graph.generate_master_graph(args.output)
    
    # README sections
    if args.readme:
        print("\n📝 README Sections:\n")
        for folder in sorted(graph.folders.keys()):
            print(graph.generate_readme_section(folder))


if __name__ == "__main__":
    main()
