"""Code Writer Service - Saves generated code to project files

Handles:
- Path validation (security: no path traversal)
- File name sanitization
- Existing file detection (ask before overwrite)
- File creation with proper error handling
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import os

logger = logging.getLogger(__name__)


class CodeWriterError(Exception):
    """Base error for code writer operations"""
    pass


class CodeWriter:
    """Service to safely write generated code to project files"""
    
    # Allowed extensions for code generation
    ALLOWED_EXTENSIONS = {
        '.python', '.py', '.js', '.ts', '.tsx', '.jsx', 
        '.go', '.rs', '.java', '.cpp', '.c', '.h',
        '.rb', '.php', '.sql', '.yaml', '.yml', '.json',
        '.txt', '.md', '.sh', '.bash', '.requirements',
        '.j2', '.jinja', '.jinja2', '.toml', '.ini', '.cfg', '.env'
    }
    
    # Max file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def __init__(self, project_root: str):
        """Initialize writer with project root
        
        Args:
            project_root: Base directory for writing files
            
        Raises:
            CodeWriterError: If project_root doesn't exist or isn't a directory
        """
        self.project_root = Path(project_root).resolve()
        
        if not self.project_root.exists():
            raise CodeWriterError(f"Project root doesn't exist: {project_root}")
        
        if not self.project_root.is_dir():
            raise CodeWriterError(f"Project root is not a directory: {project_root}")
        
        logger.info(f"CodeWriter initialized with root: {self.project_root}")
    
    def _validate_path(self, filepath: str) -> Tuple[bool, str]:
        """Validate that filepath is within project root
        
        Args:
            filepath: Relative or absolute filepath
            
        Returns:
            (is_valid, error_message)
        """
        # Resolve to absolute path
        if Path(filepath).is_absolute():
            target = Path(filepath).resolve()
        else:
            target = (self.project_root / filepath).resolve()
        
        # Check: is target within project_root?
        try:
            target.relative_to(self.project_root)
        except ValueError:
            return False, f"Path traversal detected: {filepath} is outside project root"
        
        return True, ""
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename: remove dangerous chars
        
        Args:
            filename: Original filename (e.g., "my_module.py")
            
        Returns:
            Sanitized filename
        """
        # Remove path separators that snuck in
        filename = filename.replace('/', '_').replace('\\', '_')
        
        # Keep only alphanumeric, underscores, dots, hyphens
        import re
        filename = re.sub(r'[^\w.\-]', '_', filename)
        
        # Remove leading dots (hidden files)
        filename = filename.lstrip('.')
        
        return filename
    
    def _get_extension(self, filename: str) -> str:
        """Get file extension with proper handling
        
        Args:
            filename: Filename (e.g., "generated_1.python")
            
        Returns:
            Extension with dot (e.g., ".python") or empty string
        """
        if '.' not in filename:
            return ""
        
        ext = '.' + filename.split('.')[-1]
        return ext
    
    def _check_file_exists(self, filepath: Path) -> bool:
        """Check if file already exists
        
        Args:
            filepath: Path to check
            
        Returns:
            True if exists, False otherwise
        """
        return filepath.exists()
    
    def write_code_block(self, filename: str, content: str, 
                        overwrite: bool = False) -> Dict[str, any]:
        """Write a single code block to file
        
        Args:
            filename: Filename (e.g., "my_module.py")
            content: Code content to write
            overwrite: If False, return exists error when file exists
            
        Returns:
            {
                'success': bool,
                'filepath': str (absolute path),
                'filename': str,
                'exists': bool,
                'error': str or None,
                'size': int (bytes written)
            }
        """
        try:
            # Sanitize filename
            safe_filename = self._sanitize_filename(filename)
            
            # Validate extension
            ext = self._get_extension(safe_filename)
            if ext and ext not in self.ALLOWED_EXTENSIONS:
                return {
                    'success': False,
                    'filename': filename,
                    'filepath': None,
                    'exists': False,
                    'error': f"File type not allowed: {ext}. Allowed: {self.ALLOWED_EXTENSIONS}",
                    'size': 0
                }
            
            # Build target path
            target_path = self.project_root / safe_filename
            
            # Validate path (security)
            is_valid, error_msg = self._validate_path(str(target_path))
            if not is_valid:
                return {
                    'success': False,
                    'filename': filename,
                    'filepath': str(target_path),
                    'exists': False,
                    'error': error_msg,
                    'size': 0
                }
            
            # Check file size
            if len(content) > self.MAX_FILE_SIZE:
                return {
                    'success': False,
                    'filename': filename,
                    'filepath': str(target_path),
                    'exists': False,
                    'error': f"File too large: {len(content)} > {self.MAX_FILE_SIZE}",
                    'size': 0
                }
            
            # Check if exists
            exists = self._check_file_exists(target_path)
            if exists and not overwrite:
                return {
                    'success': False,
                    'filename': filename,
                    'filepath': str(target_path),
                    'exists': True,
                    'error': f"File already exists. Use overwrite=True to replace.",
                    'size': 0
                }
            
            # Create parent directories if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            file_size = len(content)
            logger.info(f"Wrote {file_size} bytes to {target_path}")
            
            return {
                'success': True,
                'filename': safe_filename,
                'filepath': str(target_path),
                'exists': exists,
                'error': None,
                'size': file_size
            }
        
        except Exception as e:
            logger.exception(f"Error writing file {filename}")
            return {
                'success': False,
                'filename': filename,
                'filepath': None,
                'exists': False,
                'error': f"Exception: {str(e)}",
                'size': 0
            }
    
    def write_code_blocks(self, code_blocks: List[Dict], 
                         overwrite: bool = False) -> Dict[str, any]:
        """Write multiple code blocks to files
        
        Args:
            code_blocks: List of {'filename': str, 'content': str}
            overwrite: If False, skip existing files
            
        Returns:
            {
                'success': bool (all files written without errors),
                'total': int,
                'written': int,
                'files': [result dict for each file],
                'errors': [error messages if any]
            }
        """
        results = []
        errors = []
        written_count = 0
        
        for block in code_blocks:
            filename = block.get('filename', 'generated.py')
            content = block.get('content', '')
            
            result = self.write_code_block(filename, content, overwrite=overwrite)
            results.append(result)
            
            if result['success']:
                written_count += 1
            else:
                errors.append(result['error'])
        
        return {
            'success': len(errors) == 0,
            'total': len(code_blocks),
            'written': written_count,
            'files': results,
            'errors': errors
        }
