"""Project context manager for comprehensive project understanding."""
import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
import subprocess


@dataclass
class FileInfo:
    """Information about a file."""
    path: str
    relative_path: str
    size: int
    lines: int = 0
    language: str = ""
    is_config: bool = False
    is_doc: bool = False
    priority: int = 0  # Higher = more important
    content_preview: str = ""
    
    def __lt__(self, other):
        """Sort by priority (higher first), then by lines."""
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.lines > other.lines


@dataclass
class ProjectInfo:
    """Complete project information."""
    root_path: str
    name: str
    language: str  # python, javascript, go, mixed
    description: str
    files: List[FileInfo]
    dependencies: List[str]
    total_size: int
    total_files: int
    structure: str  # Tree view
    
    def to_context_string(self, max_tokens: int = 4000) -> str:
        """Convert to LLM context string.
        
        Args:
            max_tokens: Maximum tokens to use (rough estimate)
        
        Returns:
            Formatted context for LLM
        """
        lines = []
        
        # Header
        lines.append(f"# Project: {self.name}")
        lines.append(f"**Language:** {self.language}")
        lines.append(f"**Files:** {self.total_files}")
        lines.append(f"**Size:** {self.total_size / 1024:.1f} KB")
        lines.append("")
        
        # Dependencies
        if self.dependencies:
            lines.append("## Dependencies")
            for dep in self.dependencies[:10]:
                lines.append(f"- {dep}")
            if len(self.dependencies) > 10:
                lines.append(f"- ... and {len(self.dependencies) - 10} more")
            lines.append("")
        
        # Project Structure
        lines.append("## Structure")
        lines.append("```")
        lines.extend(self.structure.split('\n')[:30])
        lines.append("```")
        lines.append("")
        
        # Key Files Content
        lines.append("## Key Files Content")
        token_count = 0
        
        for file_info in self.files[:10]:  # Top 10 files
            if token_count > max_tokens * 0.8:
                break
            
            if file_info.is_doc or file_info.is_config or file_info.language in ['python', 'javascript']:
                lines.append(f"\n### {file_info.relative_path}")
                
                # Read actual content
                try:
                    with open(file_info.path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(2000)  # First 2000 chars
                        lines.append("```")
                        lines.append(content)
                        lines.append("```")
                        token_count += len(content) // 4
                except:
                    pass
        
        return "\n".join(lines)


class ProjectContextManager:
    """Manage and build project context for LLM."""
    
    # Files/dirs to ignore
    IGNORE_PATTERNS = {
        '.git', '__pycache__', 'node_modules', '.venv', 'venv',
        '.egg-info', 'dist', 'build', '.pytest_cache', '.vscode',
        '.idea', '*.pyc', '*.pyo', '.DS_Store', 'coverage',
    }
    
    # Priority mapping
    PRIORITY_FILES = {
        'README.md': 100,
        'README.rst': 100,
        'setup.py': 90,
        'pyproject.toml': 90,
        'package.json': 90,
        'requirements.txt': 85,
        'Makefile': 85,
        'Dockerfile': 85,
        '.env.example': 80,
        'config.yml': 80,
        'config.yaml': 80,
        'main.py': 75,
        'index.js': 75,
        'main.go': 75,
    }
    
    LANGUAGE_EXTENSIONS = {
        'python': {'.py', '.pyx', '.pyi'},
        'javascript': {'.js', '.jsx'},
        'typescript': {'.ts', '.tsx'},
        'go': {'.go'},
        'rust': {'.rs'},
        'java': {'.java'},
        'csharp': {'.cs'},
        'ruby': {'.rb'},
        'php': {'.php'},
    }
    
    def __init__(self, project_root: str = "."):
        """Initialize context manager.
        
        Args:
            project_root: Root directory of project
        """
        self.root = Path(project_root).resolve()
        self.project_info: Optional[ProjectInfo] = None
    
    def build_context(self) -> ProjectInfo:
        """Build complete project context.
        
        Returns:
            ProjectInfo with all project data
        """
        files = self._scan_files()
        lang = self._detect_language(files)
        deps = self._extract_dependencies()
        structure = self._build_tree_view(files)
        
        total_size = sum(f.size for f in files)
        
        project_info = ProjectInfo(
            root_path=str(self.root),
            name=self.root.name,
            language=lang,
            description=self._get_project_description(),
            files=files,
            dependencies=deps,
            total_size=total_size,
            total_files=len(files),
            structure=structure,
        )
        
        self.project_info = project_info
        return project_info
    
    def _scan_files(self) -> List[FileInfo]:
        """Scan project and collect file information."""
        files = []
        
        for path in self.root.rglob("*"):
            # Skip ignored patterns
            if any(pattern in str(path) for pattern in self.IGNORE_PATTERNS):
                continue
            
            if path.is_file():
                try:
                    size = path.stat().st_size
                    if size > 10_000_000:  # Skip huge files
                        continue
                    
                    relative_path = path.relative_to(self.root)
                    language = self._get_file_language(path)
                    is_config = self._is_config_file(path)
                    is_doc = self._is_doc_file(path)
                    priority = self.PRIORITY_FILES.get(path.name, 0)
                    
                    # Count lines for code files
                    lines = 0
                    if language and size < 100_000:
                        try:
                            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                                lines = len(f.readlines())
                        except:
                            pass
                    
                    file_info = FileInfo(
                        path=str(path),
                        relative_path=str(relative_path),
                        size=size,
                        lines=lines,
                        language=language,
                        is_config=is_config,
                        is_doc=is_doc,
                        priority=priority,
                    )
                    
                    files.append(file_info)
                
                except (OSError, PermissionError):
                    continue
        
        # Sort by priority and relevance
        files.sort()
        return files
    
    def _detect_language(self, files: List[FileInfo]) -> str:
        """Detect primary project language."""
        lang_counts = {}
        
        for file_info in files:
            if file_info.language:
                lang_counts[file_info.language] = lang_counts.get(file_info.language, 0) + 1
        
        if not lang_counts:
            return "unknown"
        
        primary = max(lang_counts, key=lang_counts.get)
        if len(lang_counts) > 1:
            return "mixed"
        return primary
    
    def _get_file_language(self, path: Path) -> str:
        """Get programming language of file."""
        suffix = path.suffix.lower()
        for lang, extensions in self.LANGUAGE_EXTENSIONS.items():
            if suffix in extensions:
                return lang
        return ""
    
    def _is_config_file(self, path: Path) -> bool:
        """Check if file is a configuration file."""
        config_extensions = {'.yaml', '.yml', '.json', '.toml', '.ini', '.cfg', '.conf'}
        config_names = {'config', 'settings', '.env'}
        
        return (path.suffix.lower() in config_extensions or
                path.stem in config_names)
    
    def _is_doc_file(self, path: Path) -> bool:
        """Check if file is documentation."""
        doc_extensions = {'.md', '.rst', '.txt'}
        return path.suffix.lower() in doc_extensions
    
    def _extract_dependencies(self) -> List[str]:
        """Extract project dependencies."""
        deps = []
        
        # Python dependencies
        req_file = self.root / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            deps.append(f"python:{line}")
            except:
                pass
        
        # pyproject.toml dependencies
        pyproject = self.root / "pyproject.toml"
        if pyproject.exists():
            try:
                with open(pyproject, 'r') as f:
                    content = f.read()
                    if 'dependencies' in content:
                        deps.append("python:pyproject.toml")
            except:
                pass
        
        # Node dependencies
        package_json = self.root / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    deps.extend([f"node:{k}" for k in data.get('dependencies', {})])
            except:
                pass
        
        return deps[:20]  # Top 20 deps
    
    def _get_project_description(self) -> str:
        """Get project description from README or setup.py."""
        readme = self.root / "README.md"
        if readme.exists():
            try:
                with open(readme, 'r') as f:
                    first_lines = ''.join(f.readlines()[:5])
                    return first_lines.strip()
            except:
                pass
        
        return f"Project: {self.root.name}"
    
    def _build_tree_view(self, files: List[FileInfo], max_depth: int = 3) -> str:
        """Build directory tree view."""
        lines = []
        
        # Group files by directory
        by_dir = {}
        for file_info in files[:50]:  # Top 50 files
            rel_path = Path(file_info.relative_path)
            if rel_path.parent == Path('.'):
                depth = 0
            else:
                depth = len(rel_path.parts) - 1
            
            if depth <= max_depth:
                if str(rel_path.parent) not in by_dir:
                    by_dir[str(rel_path.parent)] = []
                by_dir[str(rel_path.parent)].append(file_info)
        
        # Build tree
        for dir_name in sorted(by_dir.keys()):
            depth = len(dir_name.split(os.sep)) - 1
            indent = "  " * depth
            if dir_name == '.':
                lines.append(str(self.root.name) + "/")
            else:
                lines.append(f"{indent}{Path(dir_name).name}/")
            
            for file_info in by_dir[dir_name]:
                file_indent = "  " * (depth + 1)
                size_str = f" ({file_info.size / 1024:.1f}KB)" if file_info.size > 1024 else ""
                lines.append(f"{file_indent}{Path(file_info.path).name}{size_str}")
        
        return "\n".join(lines)
    
    def add_file_to_context(self, file_path: str) -> bool:
        """Add specific file to context.
        
        Args:
            file_path: Path to file
        
        Returns:
            True if added, False otherwise
        """
        if not self.project_info:
            return False
        
        path = self.root / file_path
        if path.exists() and path.is_file():
            try:
                size = path.stat().st_size
                relative_path = path.relative_to(self.root)
                language = self._get_file_language(path)
                
                file_info = FileInfo(
                    path=str(path),
                    relative_path=str(relative_path),
                    size=size,
                    language=language,
                    is_config=self._is_config_file(path),
                    is_doc=self._is_doc_file(path),
                    priority=50,
                )
                
                self.project_info.files.append(file_info)
                return True
            except:
                pass
        
        return False
    
    def get_summary(self) -> str:
        """Get readable summary of project context."""
        if not self.project_info:
            self.build_context()
        
        info = self.project_info
        return f"""
Project: {info.name}
Language: {info.language}
Files: {info.total_files}
Size: {info.total_size / 1024:.1f} KB
Dependencies: {len(info.dependencies)}
Root: {info.root_path}
"""
