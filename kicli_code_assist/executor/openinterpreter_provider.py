"""OpenInterpreter provider for code execution."""
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class OpenInterpreterConfig:
    """Configuration for OpenInterpreter."""
    model: str = "gpt-4o-mini"
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    auto_run: bool = False
    
class OpenInterpreterProvider:
    """Execution provider using OpenInterpreter."""
    
    def __init__(self, config: OpenInterpreterConfig):
        """Initialize provider.
        
        Args:
            config: OpenInterpreter configuration
        """
        self.config = config
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate configuration."""
        if not self.config.api_key:
            raise ValueError("OpenInterpreter requires an API key in ki-core config or environment")
        if not self.config.base_url:
            raise ValueError("OpenInterpreter requires a base_url in ki-core config or environment")
    
    def start_interactive(self) -> None:
        """Start interactive OpenInterpreter session."""
        try:
            from interpreter import interpreter
            import truststore
        except ImportError:
            raise ImportError("OpenInterpreter not installed. Install: pip install open-interpreter truststore")
        
        # Inject truststore for SSL handling
        try:
            truststore.inject_into_ssl()
        except ImportError:
            pass
        
        # Configure interpreter
        interpreter.llm.model = self.config.model
        interpreter.llm.api_key = self.config.api_key
        interpreter.llm.api_base = self.config.base_url
        interpreter.auto_run = self.config.auto_run
        
        print(f"✓ OpenInterpreter Configuration:")
        print(f"  Base URL: {self.config.base_url}")
        print(f"  Model: {self.config.model}\n")
        
        # Start interactive session
        interpreter.chat()
    
    def chat(self, message: str) -> str:
        """Send single message to OpenInterpreter.
        
        Args:
            message: User message
            
        Returns:
            Response from interpreter
        """
        try:
            from interpreter import interpreter
            import truststore
        except ImportError:
            raise ImportError("OpenInterpreter not installed")
        
        truststore.inject_into_ssl()
        
        interpreter.llm.model = self.config.model
        interpreter.llm.api_key = self.config.api_key
        interpreter.llm.api_base = self.config.base_url
        
        # Send message and collect response
        response_text = ""
        for chunk in interpreter._streaming_chat(message=message):
            if hasattr(chunk, 'content'):
                response_text += chunk.content
        
        return response_text
