"""
Phase 5.3-5.4: Code Implementation Agent

Analyzes external projects and implements goals by:
1. Reading existing code structure
2. Understanding requirements from documentation
3. Generating implementation code via LLM
4. Writing and verifying changes
5. Git workflow integration (5.4.1)
"""

import logging
import ast
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from kicli_code_assist.agent.git_manager import GitManager

logger = logging.getLogger(__name__)


@dataclass
class CodeFile:
    """Represents a Python code file with analysis."""
    path: Path
    content: str
    ast_tree: Optional[ast.AST] = None
    classes: List[str] = None
    functions: List[str] = None
    imports: List[str] = None
    
    def __post_init__(self):
        """Parse AST and extract structure."""
        self.classes = []
        self.functions = []
        self.imports = []
        
        try:
            self.ast_tree = ast.parse(self.content)
            
            # Extract classes and functions
            for node in ast.walk(self.ast_tree):
                if isinstance(node, ast.ClassDef):
                    self.classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    self.functions.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        self.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.imports.append(node.module)
        except SyntaxError as e:
            logger.warning(f"Cannot parse {self.path}: {e}")


@dataclass
class ProjectCodeStructure:
    """Represents analyzed project code structure."""
    project_root: Path
    python_files: List[CodeFile]
    main_modules: List[str]
    summary: str


@dataclass
class GeneratedCode:
    """Represents generated code ready to implement."""
    goal_title: str
    target_file: Path
    code_content: str
    description: str
    imports_to_add: List[str]


class CodeImplementationAgent:
    """Analyzes code structure and prepares for implementation."""
    
    def __init__(self, project_root: str):
        """Initialize with project root."""
        self.project_root = Path(project_root)
        self.code_files: Dict[str, CodeFile] = {}
        
    def discover_python_files(self, max_files: int = 50) -> List[Path]:
        """Discover Python files in project."""
        py_files = list(self.project_root.rglob("*.py"))
        
        # Filter out common directories
        excluded = {".venv", "venv", ".git", "__pycache__", ".pytest_cache", "node_modules"}
        py_files = [f for f in py_files if not any(ex in f.parts for ex in excluded)]
        
        return sorted(py_files)[:max_files]
    
    def read_and_analyze_files(self, file_paths: Optional[List[Path]] = None) -> ProjectCodeStructure:
        """Read Python files and analyze structure."""
        if file_paths is None:
            file_paths = self.discover_python_files()
        
        logger.info(f"Analyzing {len(file_paths)} Python files in {self.project_root}")
        
        code_files = []
        for file_path in file_paths:
            try:
                content = file_path.read_text(encoding="utf-8")
                code_file = CodeFile(path=file_path, content=content)
                self.code_files[str(file_path)] = code_file
                code_files.append(code_file)
            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")
        
        # Identify main modules (files in top-level dirs)
        main_modules = set()
        for cf in code_files:
            rel_path = cf.path.relative_to(self.project_root)
            if len(rel_path.parts) == 2:  # e.g., ki_knowledge/cli.py
                main_modules.add(rel_path.parts[0])
        
        # Generate summary
        summary_lines = [
            f"Project: {self.project_root.name}",
            f"Python files: {len(code_files)}",
            f"Main modules: {', '.join(sorted(main_modules))}" if main_modules else "",
        ]
        summary = "\n".join(l for l in summary_lines if l)
        
        return ProjectCodeStructure(
            project_root=self.project_root,
            python_files=code_files,
            main_modules=sorted(main_modules),
            summary=summary
        )
    
    def get_file_for_goal(self, goal_title: str, goal_description: str) -> Optional[CodeFile]:
        """Find most relevant file for a goal based on goal keywords."""
        goal_keywords = (goal_title.lower() + " " + goal_description.lower()).split()
        
        best_match = None
        best_score = 0
        
        for code_file in self.code_files.values():
            rel_path = str(code_file.path.relative_to(self.project_root)).lower()
            
            # Score based on keyword matches in path
            score = sum(1 for kw in goal_keywords if kw in rel_path)
            
            # Extra score for common patterns
            if "cli" in goal_keywords and "cli" in rel_path:
                score += 5
            if "command" in goal_keywords and ("command" in rel_path or "cmd" in rel_path):
                score += 5
            
            if score > best_score:
                best_score = score
                best_match = code_file
        
        return best_match
    
    def get_goal_implementation_context(self, goal_title: str, goal_description: str) -> Dict[str, Any]:
        """Gather context needed for implementing a goal."""
        # Find relevant files
        primary_file = self.get_file_for_goal(goal_title, goal_description)
        
        context = {
            "goal_title": goal_title,
            "goal_description": goal_description,
            "project_structure": {
                "root": str(self.project_root),
                "main_modules": list(self.code_files.keys())[:5],  # Top 5 files
            },
            "relevant_file": None,
            "code_snippet": "",
            "imports_needed": [],
            "related_classes": [],
            "related_functions": [],
        }
        
        if primary_file:
            context["relevant_file"] = str(primary_file.path.relative_to(self.project_root))
            context["code_snippet"] = primary_file.content[:500] + "..." if len(primary_file.content) > 500 else primary_file.content
            context["imports_needed"] = primary_file.imports[:5]
            context["related_classes"] = primary_file.classes[:5]
            context["related_functions"] = primary_file.functions[:5]
        
        return context
    
    def generate_implementation_prompt(self, goal_title: str, goal_description: str, 
                                       requirements: List[str], context: Dict[str, Any]) -> str:
        """Generate LLM prompt for code implementation."""
        prompt = f"""## Code Implementation Task

**Goal:** {goal_title}

**Description:** {goal_description}

**Requirements:**
{chr(10).join(f"- {req}" for req in requirements[:5])}

**Project Context:**
- Root: {context['project_structure']['root']}
- Main modules: {', '.join(context['project_structure']['main_modules'][:3])}

**Relevant File:** {context['relevant_file'] or 'Not identified'}

**Existing Code Structure:**
```python
{context['code_snippet']}
```

**Task:**
1. Analyze the existing code structure
2. Identify where new code should be added
3. Generate Python code to implement the goal
4. Ensure compatibility with existing code

**Response Format:**
- Provide complete, ready-to-use Python code
- Include necessary imports
- Add docstrings for new functions/classes
- Keep code style consistent with the project
"""
        return prompt
    
    def generate_code_via_llm(self, goal_title: str, goal_description: str, 
                              requirements: List[str], api_client=None) -> Optional[GeneratedCode]:
        """Use LLM to generate implementation code.
        
        Args:
            goal_title: Goal name
            goal_description: Detailed goal description
            requirements: List of requirements
            api_client: Optional ki-core AIClient for LLM calls
            
        Returns:
            GeneratedCode object or None if generation fails
        """
        # Try to use ki-core AIClient if available
        if api_client is None:
            try:
                from ki_core.core.client import AIClient
                from ki_core.adapters.openai import OpenAIClient
                from ki_core.config import ConfigManager
                
                config = ConfigManager()
                api_client = OpenAIClient(config.llm_config)
            except Exception as e:
                logger.warning(f"Cannot initialize LLM client: {e}")
                return None
        
        # Gather context
        context = self.get_goal_implementation_context(goal_title, goal_description)
        
        # Generate prompt
        prompt = self.generate_implementation_prompt(goal_title, goal_description, requirements, context)
        
        # Call LLM
        try:
            from ki_core.core.models import ChatRequest, ChatMessage
            
            request = ChatRequest(
                messages=[
                    ChatMessage(role="system", content="You are an expert Python developer helping implement features in a software project."),
                    ChatMessage(role="user", content=prompt)
                ],
                model="claude-3-5-sonnet",
                temperature=0.3,
                max_tokens=2000
            )
            
            response = api_client.chat(request)
            
            # Find relevant file
            target_file = self.get_file_for_goal(goal_title, goal_description)
            if not target_file:
                # Create new file if no existing file found
                module_name = goal_title.lower().replace(" ", "_")
                target_file_path = self.project_root / "ki_knowledge" / "commands" / f"{module_name}.py"
            else:
                target_file_path = target_file.path
            
            return GeneratedCode(
                goal_title=goal_title,
                target_file=target_file_path,
                code_content=response.content,
                description=f"Generated code for: {goal_title}",
                imports_to_add=context.get("imports_needed", [])
            )
        
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return None
    
    def apply_generated_code(self, generated_code: GeneratedCode, dry_run: bool = True) -> Dict[str, Any]:
        """Apply generated code to project files.
        
        Args:
            generated_code: GeneratedCode object from LLM
            dry_run: If True, don't actually write files, just show what would happen
            
        Returns:
            Dict with success status, file written, changes made
        """
        result = {
            "success": False,
            "file": str(generated_code.target_file),
            "dry_run": dry_run,
            "changes_made": [],
            "error": None
        }
        
        try:
            # Check if target file exists
            if generated_code.target_file.exists():
                # Append to existing file
                existing_content = generated_code.target_file.read_text(encoding="utf-8")
                
                # Extract function/class names from generated code
                generated_lines = generated_code.code_content.split("\n")
                
                # Only append new definitions (not duplicates)
                new_lines = []
                for line in generated_lines:
                    if line.startswith("def ") or line.startswith("class "):
                        # Check if this is already in the file
                        if line not in existing_content:
                            new_lines.append(line)
                
                if new_lines:
                    combined_content = existing_content + "\n\n# Generated implementation\n" + generated_code.code_content
                    
                    if not dry_run:
                        generated_code.target_file.write_text(combined_content, encoding="utf-8")
                    
                    result["success"] = True
                    result["changes_made"].append(f"Appended code to {generated_code.target_file.name}")
                else:
                    result["error"] = "No new code to add (definitions already exist)"
            else:
                # Create new file
                generated_code.target_file.parent.mkdir(parents=True, exist_ok=True)
                
                if not dry_run:
                    generated_code.target_file.write_text(generated_code.code_content, encoding="utf-8")
                
                result["success"] = True
                result["changes_made"].append(f"Created new file: {generated_code.target_file}")
        
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error applying generated code: {e}")
        
        return result
    
    def verify_implementation(self, goal_title: str, generated_code: GeneratedCode) -> Dict[str, Any]:
        """Verify that generated code is syntactically correct and imports work.
        
        Args:
            goal_title: Goal name for reference
            generated_code: GeneratedCode object to verify
            
        Returns:
            Dict with verification results
        """
        result = {
            "goal": goal_title,
            "valid_syntax": False,
            "imports_ok": False,
            "warnings": [],
            "errors": []
        }
        
        try:
            # Check syntax
            ast.parse(generated_code.code_content)
            result["valid_syntax"] = True
        except SyntaxError as e:
            result["errors"].append(f"Syntax error: {e}")
        
        # Try to check imports
        try:
            for imp in generated_code.imports_to_add:
                try:
                    __import__(imp)
                    result["imports_ok"] = True
                except ImportError:
                    result["warnings"].append(f"Import not available: {imp}")
        except Exception as e:
            result["warnings"].append(f"Cannot verify imports: {e}")
        
        return result
    
    def apply_with_git(self, goal_title: str, goal_description: str,
                       generated_code: GeneratedCode, push_to_remote: bool = True) -> Dict[str, Any]:
        """
        Apply generated code with full git workflow (Phase 5.4.1).
        
        Implements:
        1. Create feature branch
        2. Write code to files
        3. Verify implementation
        4. Commit changes
        5. Push to remote
        
        Args:
            goal_title: Goal being implemented
            goal_description: Detailed description of what was implemented
            generated_code: GeneratedCode object with code to apply
            push_to_remote: Whether to push to remote (default: True)
        
        Returns:
            Dict with implementation workflow results
        """
        result = {
            "success": False,
            "goal": goal_title,
            "steps": {},
            "branch": None,
            "commit_sha": None,
            "errors": []
        }
        
        try:
            # Step 1: Initialize git manager
            logger.info(f"🔄 Starting git workflow for: {goal_title}")
            git = GitManager(str(self.project_root))
            
            # Step 2: Create feature branch
            logger.info("📍 Creating feature branch...")
            if not git.create_branch(goal_title):
                result["errors"].append("Failed to create branch")
                return result
            
            branch_name = git.get_current_branch()
            result["branch"] = branch_name
            result["steps"]["branch_created"] = True
            logger.info(f"✓ Branch: {branch_name}")
            
            # Step 3: Apply code changes
            logger.info("📝 Applying code changes...")
            apply_result = self.apply_generated_code(generated_code, dry_run=False)
            if not apply_result.get("success"):
                result["errors"].append("Failed to apply code")
                git.reset_branch(keep_changes=True)
                return result
            
            result["steps"]["code_applied"] = True
            
            # Extract just filenames from changes_made messages
            changes = apply_result.get("changes_made", [])
            files_to_add = []
            for change in changes:
                # Extract filename from "Created new file: /path/to/file" or similar
                if ":" in change:
                    filename = change.split(":", 1)[1].strip()
                else:
                    filename = change
                files_to_add.append(filename)
            
            result["files_written"] = files_to_add
            logger.info(f"✓ Code applied to {len(files_to_add)} file(s)")
            
            # Step 4: Verify implementation
            logger.info("✅ Verifying implementation...")
            verification = self.verify_implementation(goal_title, generated_code)
            if not verification.get("valid_syntax"):
                result["errors"].append(f"Invalid syntax: {verification.get('errors', [])}")
                git.reset_branch(keep_changes=True)
                return result
            
            result["steps"]["verified"] = True
            result["verification"] = verification
            logger.info("✓ Verification passed")
            
            # Step 5: Commit changes
            logger.info("💾 Committing changes...")
            commit_sha = git.commit_changes(
                goal_title,
                goal_description,
                files_to_add
            )
            if not commit_sha:
                result["errors"].append("Failed to commit")
                git.reset_branch(keep_changes=True)
                return result
            
            result["commit_sha"] = commit_sha
            result["steps"]["committed"] = True
            logger.info(f"✓ Committed: {commit_sha[:8]}")
            
            # Step 6: Push to remote
            if push_to_remote:
                logger.info("🚀 Pushing to remote...")
                if not git.push_to_remote(branch_name):
                    result["errors"].append("Failed to push to remote")
                    result["steps"]["pushed"] = False
                else:
                    result["steps"]["pushed"] = True
                    logger.info(f"✓ Pushed to origin/{branch_name}")
            
            # Step 7: Generate PR info
            logger.info("📋 Generating PR information...")
            pr_info = git.create_pull_request_info(goal_title, goal_description)
            result["pull_request_info"] = pr_info
            result["steps"]["pr_ready"] = True
            logger.info(f"✓ PR ready: '{pr_info['title']}'")
            
            # Success!
            result["success"] = True
            logger.info(f"✅ Git workflow complete for: {goal_title}")
            
        except Exception as e:
            logger.error(f"Git workflow error: {e}", exc_info=True)
            result["errors"].append(str(e))
        
        return result



