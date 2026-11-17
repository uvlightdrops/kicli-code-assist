"""
Phase I3: Code Generation Routes

Multi-turn code generation for empty projects via LLM.
Supports iterative refinement of generated code.
Supports multi-file code generation with smart parsing.

Routes:
- POST /api/code/generate - Generate code based on requirements
"""

import logging
import uuid
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from flask import jsonify, request

# LLM Client imports
from ki_core.core.models import ChatRequest, Message, Role, StreamEvent, StreamEventType
from ki_core.adapters.mock import MockAIClient
from ki_core.adapters.openai_compat import OpenAICompatibleClient
from kicli_code_assist.app_config import AppConfig
from kicli_code_assist.services.code_writer import CodeWriter, CodeWriterError
from kicli_code_assist.services.chat_history import ChatHistoryManager

logger = logging.getLogger(__name__)

# Chat history manager (persistent storage)
_chat_history = ChatHistoryManager()

# LLM client (cached)
_llm_client = None


def get_llm_client():
    """Get or create LLM client."""
    global _llm_client
    
    if _llm_client is not None:
        return _llm_client
    
    # Try to load credentials from creds.yaml
    openai_api_key = None
    openai_base_url = "https://api.openai.com/v1"
    openai_model = "gpt-4o-mini"
    
    try:
        import yaml
        creds_path = Path.cwd() / "creds.yaml"
        if creds_path.exists():
            with open(creds_path, 'r') as f:
                creds = yaml.safe_load(f)
                openai_cfg = creds.get("llm", {}).get("providers", {}).get("openai", {})
                openai_api_key = openai_cfg.get("api_key")
                openai_base_url = openai_cfg.get("base_url", openai_base_url)
                openai_model = openai_cfg.get("model", openai_model)
                logger.info(f"Loaded OpenAI config from creds.yaml")
    except Exception as e:
        logger.warning(f"Could not load creds.yaml: {e}")
    
    # Also try AppConfig (in case it's set via env vars)
    if not openai_api_key:
        try:
            config = AppConfig.from_env()
            openai_api_key = config.openai_api_key
            openai_base_url = config.openai_base_url or openai_base_url
            openai_model = config.openai_model or openai_model
        except Exception as e:
            logger.warning(f"Could not load AppConfig: {e}")
    
    # If we have API key, use real OpenAI
    if openai_api_key:
        try:
            logger.info(f"Using OpenAI client for code generation (model: {openai_model})")
            _llm_client = OpenAICompatibleClient(
                base_url=openai_base_url,
                api_key=openai_api_key,
                model=openai_model,
            )
            return _llm_client
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")
    
    # Fallback: use demo client
    logger.info("Using Demo client for code generation (no OpenAI credentials found)")
    _llm_client = DemoAIClient()
    return _llm_client


class DemoAIClient:
    """Demo client that returns realistic code samples."""
    
    def chat_stream(self, request: ChatRequest):
        """Return demo code responses with context awareness."""
        
        # Extract conversation history
        history_text = ""
        user_message = ""
        
        for msg in request.messages:
            if msg.role == Role.USER:
                # Get the last user message (which is the actual request, not the system prompt)
                user_message = msg.content
        
        # Detect intent from user message
        message_lower = user_message.lower()
        
        # Determine what to do based on keywords
        response = None
        
        # Handle "save" / "write" / "file" requests
        if any(word in message_lower for word in ["save", "write", "file", "speichern", "datei"]):
            response = '''I'll save that code to a file for you.

```python
# File: is_prime.py

def is_prime(n: int) -> bool:
    """Check if a number is prime.
    
    Args:
        n: The number to check
        
    Returns:
        True if n is prime, False otherwise
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


if __name__ == "__main__":
    # Test cases
    print(f"is_prime(17) = {is_prime(17)}")  # True
    print(f"is_prime(24) = {is_prime(24)}")  # False
    print(f"is_prime(2) = {is_prime(2)}")    # True
```

This file has been saved as `is_prime.py` in your project directory. You can run it with:
```bash
python is_prime.py
```
'''
        
        # Handle "refactor" / "improve" requests
        elif any(word in message_lower for word in ["refactor", "improve", "optimize", "verbessern"]):
            response = '''Here's an optimized version with better performance:

```python
def is_prime(n: int) -> bool:
    """
    Optimized prime checker using trial division.
    Time complexity: O(sqrt(n))
    """
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True
```

This version checks divisibility by 2 and 3 first, then checks numbers of form 6k±1, which is faster.
'''
        
        # Handle "test" / "add test" requests
        elif any(word in message_lower for word in ["test", "unittest", "pytest", "testen"]):
            response = '''Here's a test suite for the prime function:

```python
import unittest

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


class TestIsPrime(unittest.TestCase):
    def test_small_primes(self):
        self.assertTrue(is_prime(2))
        self.assertTrue(is_prime(3))
        self.assertTrue(is_prime(5))
    
    def test_non_primes(self):
        self.assertFalse(is_prime(0))
        self.assertFalse(is_prime(1))
        self.assertFalse(is_prime(4))
        self.assertFalse(is_prime(6))
    
    def test_large_prime(self):
        self.assertTrue(is_prime(97))
        self.assertTrue(is_prime(1009))
    
    def test_large_non_prime(self):
        self.assertFalse(is_prime(100))
        self.assertFalse(is_prime(1000))

if __name__ == "__main__":
    unittest.main()
```

Run tests with: `python -m unittest test_is_prime.py`
'''
        
        # Handle "prime" request specifically
        elif "prime" in message_lower:
            response = '''Here's a Python function to check if a number is prime:

```python
def is_prime(n: int) -> bool:
    """Check if a number is prime.
    
    Args:
        n: The number to check
        
    Returns:
        True if n is prime, False otherwise
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True
```

Usage example:
```python
print(is_prime(17))  # True
print(is_prime(24))  # False
```
'''
        
        # Handle FastAPI request
        elif any(word in message_lower for word in ["fastapi", "api", "server", "health"]):
            response = '''Here's a FastAPI server with health check:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Demo API", version="1.0.0")

class HealthResponse(BaseModel):
    status: str
    version: str

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Demo API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Run with: `uvicorn main:app --reload`
'''
        
        # Default generic response
        if response is None:
            response = f'''I can help you generate code. Based on your request: "{user_message}"

Common requests I can help with:
- **Prime function**: Generate a prime number checker
- **Save/write**: Save code to a file
- **Improve/optimize**: Refactor existing code
- **Tests**: Generate test cases
- **FastAPI**: Create a REST API server

Please ask me to generate code for one of these!
'''
        
        # Stream the response character by character
        for char in response:
            yield StreamEvent(type=StreamEventType.TOKEN, text=char)
        
        yield StreamEvent(type=StreamEventType.DONE)


def extract_multifile_code_blocks(response_text: str, default_ext: str = "python") -> List[Dict[str, str]]:
    """Extract multiple files from LLM response using "# File: name" markers.
    
    Format expected from LLM:
    ---
    # File: main.py
    ```python
    code here
    ```
    
    ---
    # File: utils.py
    ```python
    more code
    ```
    
    Args:
        response_text: LLM response text
        default_ext: Default extension if not specified
    
    Returns:
        List of dicts with 'filename' and 'content' keys
    """
    code_blocks = []
    
    # Split by file markers "---\n# File:"
    file_sections = re.split(r'---\n+#\s*File:\s*', response_text)
    
    for section in file_sections:
        if not section.strip():
            continue
        
        # First line should be filename
        lines = section.split('\n', 1)
        if len(lines) < 2:
            continue
        
        filename = lines[0].strip()
        rest = lines[1] if len(lines) > 1 else ""
        
        # Extract code from markdown blocks
        # Pattern: ```lang\ncode\n```
        code_pattern = r'```(\w+)?\n(.*?)\n```'
        matches = list(re.finditer(code_pattern, rest, re.DOTALL))
        
        if matches:
            # Use first code block found
            match = matches[0]
            lang = match.group(1) or default_ext
            content = match.group(2)
            
            # Ensure filename has extension
            if not any(filename.endswith(f'.{ext}') for ext in ['py', 'js', 'ts', 'go', 'rs', 'java', 'cpp', 'txt', 'md', 'json', 'yaml', 'yml', 'xml', 'html', 'css']):
                # Add extension based on language
                lang_to_ext = {
                    'python': 'py',
                    'javascript': 'js',
                    'typescript': 'ts',
                    'go': 'go',
                    'rust': 'rs',
                    'java': 'java',
                    'cpp': 'cpp',
                    'bash': 'sh',
                    'shell': 'sh',
                    'yaml': 'yaml',
                    'json': 'json',
                    'xml': 'xml',
                    'html': 'html',
                    'css': 'css',
                    'text': 'txt',
                    'plain': 'txt'
                }
                ext = lang_to_ext.get(lang, 'txt')
                filename = f"{filename}.{ext}" if '.' not in filename else filename
            
            code_blocks.append({
                "filename": filename,
                "content": content
            })
            
            logger.info(f"Extracted file: {filename} ({len(content)} bytes)")
    
    return code_blocks


def generate_code_prompt(message: str, project_root: str, file_type: str, context: str = "") -> str:
    """Generate a prompt for code generation.
    
    Instructs LLM to generate multiple files with clear naming convention.
    """
    prompt = f"""You are a code generation expert. Generate high-quality production-ready code based on the user's requirements.

## User Request:
{message}

## Context:
- Project root: {project_root}
- Target language: {file_type}
{f"- Additional context: {context}" if context else ""}

## Instructions:
1. Generate complete, production-ready code
2. Include necessary imports and dependencies
3. Add docstrings and comments for clarity
4. Follow best practices for the language
5. Make the code modular and reusable
6. When generating multiple files, clearly separate them

## Response Format:

For SINGLE file: Use a markdown code block:
```{file_type}
your code here
```

For MULTIPLE files: Use this format with file names clearly marked:

---
# File: filename1.ext
```{file_type}
code for file 1
```

---
# File: filename2.ext
```{file_type}
code for file 2
```

---
# File: requirements.txt
numpy==1.24.0
flask==2.3.0
```

IMPORTANT:
- Always use "# File: <name>" to mark each file clearly
- Use the separator "---" between files
- Include file extensions (.py, .js, .txt, etc.)
- Each file should be in its own markdown code block
- For requirements, dependencies, config files, use appropriate extensions
"""
    return prompt


def register_code_generation_routes(app):
    """Register code generation routes.
    
    Args:
        app: Flask app instance
    """
    
    @app.route("/api/code/generate", methods=["POST"])
    def code_generate():
        """
        Generate code based on user requirements.
        
        Supports multi-turn conversations for iterative code refinement.
        
        Request:
        {
            "message": "Create a Python FastAPI server with health check",
            "project_root": "/path/to/project",
            "conversation_id": "uuid-or-null",  # null creates new conversation
            "file_type": "python"  # optional: python, javascript, go, etc.
        }
        
        Response (Success):
        {
            "success": true,
            "conversation_id": "uuid",
            "response": "Here's a FastAPI server...",
            "code_blocks": [
                {
                    "filename": "main.py",
                    "content": "from fastapi import..."
                }
            ],
            "thinking": "I'll create a simple FastAPI app..."
        }
        
        Response (Error):
        {
            "success": false,
            "error": "message",
            "conversation_id": "uuid"
        }
        """
        try:
            data = request.get_json()
            
            # Validate request
            message = data.get("message", "").strip()
            if not message:
                return jsonify({
                    "success": False,
                    "error": "Missing 'message' field"
                }), 400
            
            project_root = data.get("project_root", str(Path.cwd()))
            conversation_id = data.get("conversation_id")
            file_type = data.get("file_type", "python")
            
            # Create new conversation if not provided
            if not conversation_id:
                conversation_id = _chat_history.create_conversation(project_root)
            
            logger.info(f"Code generation request: conv={conversation_id}, msg_len={len(message)}")
            
            # Load existing conversation or create if first message
            conversation = _chat_history.load_conversation(conversation_id)
            if not conversation:
                conversation_id = _chat_history.create_conversation(project_root)
            
            # Add user message to history
            _chat_history.add_message(conversation_id, "user", message)
            
            # Build conversation history from storage
            conversation = _chat_history.load_conversation(conversation_id)
            history = conversation.get("messages", []) if conversation else []
            
            # Generate prompt and call LLM
            prompt = generate_code_prompt(message, project_root, file_type)
            
            # Build messages for LLM (include conversation history)
            messages = []
            
            # Add conversation history (every 2nd message alternates user/assistant)
            for hist_msg in history[:-1]:  # Exclude the message we just added
                role = Role.ASSISTANT if hist_msg["role"] == "assistant" else Role.USER
                messages.append(Message(role=role, content=hist_msg["content"]))
            
            # Add current user message with prompt
            messages.append(Message(role=Role.USER, content=prompt))
            
            # Call LLM
            logger.info(f"Calling LLM for code generation: {len(messages)} messages in history")
            client = get_llm_client()
            
            try:
                response_text = ""
                request_obj = ChatRequest(messages=messages)
                
                # Stream response from LLM
                for event in client.chat_stream(request_obj):
                    if event.text:
                        response_text += event.text
                
                logger.info(f"LLM generated {len(response_text)} chars of code")
                
                # Extract code blocks from response
                code_blocks = []
                import re
                
                # First try: Multi-file format with "# File: name" markers
                # Pattern: "---\n# File: name\n```lang\ncode\n```"
                code_blocks = extract_multifile_code_blocks(response_text, file_type)
                
                # Fallback: Look for simple markdown code blocks (```language...```)
                if not code_blocks:
                    pattern = r"```(\w+)\n(.*?)\n```"
                    matches = re.finditer(pattern, response_text, re.DOTALL)
                    
                    block_num = 1
                    for match in matches:
                        file_ext = match.group(1)
                        content = match.group(2)
                        code_blocks.append({
                            "filename": f"generated_{block_num}.{file_ext}",
                            "content": content
                        })
                        block_num += 1
                
                # Second fallback: Look for common code start patterns
                if not code_blocks:
                    lines = response_text.split('\n')
                    code_lines = []
                    in_code = False
                    
                    for line in lines:
                        # Start of code: lines starting with common code keywords
                        if any(line.strip().startswith(kw) for kw in ['def ', 'class ', 'import ', 'from ', '#!/', 'function', 'const ', 'var ', 'let ']):
                            in_code = True
                        
                        if in_code:
                            code_lines.append(line)
                            # End of code: blank line after code section
                            if line.strip() == '' and len(code_lines) > 3:
                                break
                    
                    # If we found code lines, use them
                    if code_lines and len(''.join(code_lines)) > 20:
                        code_blocks = [{
                            "filename": f"generated.{file_type}",
                            "content": '\n'.join(code_lines).strip()
                        }]
                
                # Last fallback: use first N characters of response as code
                if not code_blocks:
                    # For MockAIClient which returns text without spaces, we show the full response
                    # In production with real LLM, this won't happen
                    code_blocks = [{
                        "filename": f"generated.{file_type}",
                        "content": response_text[:1000]  # First 1000 chars
                    }]
                
            except Exception as llm_error:
                logger.error(f"LLM call failed: {llm_error}", exc_info=True)
                response_text = f"Error generating code: {str(llm_error)}"
                code_blocks = [{
                    "filename": f"error.{file_type}",
                    "content": f"# Failed to generate code\n# Error: {str(llm_error)}"
                }]
            
            # Add assistant response to history
            files_generated = []
            for block in code_blocks:
                files_generated.append({
                    "filename": block.get("filename", "unknown"),
                    "size": len(block.get("content", "")),
                    "saved": False,  # Will be updated when actually saved
                    "saved_path": None
                })
            
            _chat_history.add_message(
                conversation_id,
                "assistant",
                response_text,
                files_generated=files_generated
            )
            
            logger.info(f"Code generation completed: conv={conversation_id}, blocks={len(code_blocks)}")
            
            return jsonify({
                "success": True,
                "conversation_id": conversation_id,
                "response": response_text,
                "code_blocks": code_blocks,
                "thinking": f"Generated {len(code_blocks)} code block(s) using LLM"
            }), 200
        
        except Exception as e:
            logger.error(f"Code generation error: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "error": str(e),
                "conversation_id": conversation_id if 'conversation_id' in locals() else None
            }), 500
    
    @app.route("/api/code/conversations/<conversation_id>", methods=["GET"])
    def get_conversation(conversation_id):
        """Get conversation history from persistent storage.
        
        Args:
            conversation_id: UUID of conversation
        
        Returns:
            {
                "success": true,
                "conversation": {...}
            }
        """
        try:
            conversation = _chat_history.load_conversation(conversation_id)
            
            if not conversation:
                return jsonify({
                    "success": False,
                    "error": f"Conversation '{conversation_id}' not found"
                }), 404
            
            return jsonify({
                "success": True,
                "conversation": conversation
            }), 200
        
        except Exception as e:
            logger.error(f"Get conversation error: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route("/api/code/conversations/<conversation_id>", methods=["DELETE"])
    def delete_conversation(conversation_id):
        """Delete conversation from persistent storage.
        
        Args:
            conversation_id: UUID of conversation
        
        Returns:
            {
                "success": true
            }
        """
        try:
            deleted = _chat_history.delete_conversation(conversation_id)
            
            if not deleted:
                return jsonify({
                    "success": False,
                    "error": f"Conversation '{conversation_id}' not found"
                }), 404
            
            return jsonify({
                "success": True
            }), 200
        
        except Exception as e:
            logger.error(f"Delete conversation error: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route("/api/code/save", methods=["POST"])
    def save_code():
        """
        Save generated code blocks to files in the project directory.
        
        Request:
        {
            "conversation_id": "uuid",
            "project_root": "/path/to/project",
            "overwrite": false  # optional: whether to overwrite existing files
        }
        
        Response (Success):
        {
            "success": true,
            "written": 2,
            "total": 2,
            "files": [
                {
                    "filename": "my_module.py",
                    "filepath": "/path/to/project/my_module.py",
                    "success": true,
                    "size": 1234
                }
            ]
        }
        
        Response (Errors):
        {
            "success": false,
            "written": 1,
            "total": 2,
            "files": [...],
            "errors": ["File 'existing.py' already exists"]
        }
        """
        try:
            data = request.get_json()
            
            # Validate request
            conversation_id = data.get("conversation_id", "").strip()
            if not conversation_id:
                return jsonify({
                    "success": False,
                    "error": "Missing 'conversation_id' field"
                }), 400
            
            # Load conversation from persistent storage
            conversation = _chat_history.load_conversation(conversation_id)
            if not conversation:
                return jsonify({
                    "success": False,
                    "error": f"Conversation '{conversation_id}' not found"
                }), 404
            
            # Extract code blocks from conversation history
            code_blocks = []
            for msg in conversation.get("messages", []):
                if msg["role"] == "assistant" and "files_generated" in msg:
                    # Reconstruct code blocks from files_generated metadata
                    # We need to find the actual content from the message
                    # For now, we store the actual content in the message itself
                    pass
            
            # Alternative: Store code_blocks in the message for now
            # (TODO: improve this to store content separately)
            assistant_messages = [m for m in conversation.get("messages", []) if m["role"] == "assistant"]
            
            # For now, we'll need to get code_blocks from the last generate call
            # This is a limitation of current design - we should improve this
            # by storing code blocks separately
            
            if not assistant_messages:
                return jsonify({
                    "success": False,
                    "error": "No assistant responses in conversation"
                }), 400
            
            # Get parameters
            project_root = data.get("project_root", str(Path.cwd()))
            overwrite = data.get("overwrite", False)
            
            # NOTE: We need the code_blocks from the most recent generation
            # For now, they should come with the save request
            code_blocks = data.get("code_blocks", [])
            
            if not code_blocks:
                return jsonify({
                    "success": False,
                    "error": "No code blocks provided in request"
                }), 400
            
            logger.info(f"Saving {len(code_blocks)} code blocks to {project_root}")
            
            # Initialize writer and save
            try:
                writer = CodeWriter(project_root)
                result = writer.write_code_blocks(code_blocks, overwrite=overwrite)
                
                # Update conversation history with saved file paths
                for file_result in result.get('files', []):
                    if file_result.get('success'):
                        # Mark file as saved in history
                        for msg in conversation.get("messages", []):
                            if msg["role"] == "assistant" and "files_generated" in msg:
                                for file_info in msg["files_generated"]:
                                    if file_info.get("filename") == file_result.get("filename"):
                                        file_info["saved"] = True
                                        file_info["saved_path"] = file_result.get("filepath")
                
                # Save updated conversation back to storage
                _chat_history._save_conversation(conversation_id, conversation)
                
                return jsonify({
                    "success": result['success'],
                    "written": result['written'],
                    "total": result['total'],
                    "files": result['files'],
                    "errors": result['errors'] if result['errors'] else None
                }), (200 if result['success'] else 400)
            
            except CodeWriterError as e:
                logger.error(f"CodeWriter error: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 400
        
        except Exception as e:
            logger.error(f"Save code error: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "error": f"Exception: {str(e)}"
            }), 500
