"""Simple chat example with ki-core integration."""
import sys
import os
from ki_core import Config
from ki_core.adapters.mock import MockAIClient
from ki_core.adapters.ollama import OllamaClient
from ki_core.adapters.openai_compat import OpenAICompatibleClient
from ki_core.core.models import ChatRequest, Message, Role


def create_client(config: Config, provider: str = "mock"):
    """Create LLM client based on provider choice.
    
    Args:
        config: ki-core Config object
        provider: 'mock', 'ollama', or 'openai'
    """
    if provider == "mock":
        return MockAIClient()
    elif provider == "ollama":
        return OllamaClient(
            base_url=config.ollama_base_url,
            model=config.ollama_model
        )
    elif provider == "openai":
        if not config.openai_api_key:
            print("ERROR: OPENAI_API_KEY not set")
            sys.exit(1)
        return OpenAICompatibleClient(
            base_url=config.openai_base_url,
            api_key=config.openai_api_key,
            model=config.openai_model
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")


def run_chat(provider: str = "mock", model: str = None):
    """Simple interactive chat with ki-core integration.
    
    Args:
        provider: LLM provider ('mock', 'ollama', 'openai')
        model: Override model name
    """
    # Load config from YAML + environment
    config = Config.from_env()
    
    # Create client
    try:
        client = create_client(config, provider)
    except Exception as e:
        print(f"ERROR: Failed to create {provider} client: {e}")
        sys.exit(1)
    
    # Determine actual model being used
    if model:
        actual_model = model
    elif provider == "ollama":
        actual_model = config.ollama_model
    elif provider == "openai":
        actual_model = config.openai_model
    else:
        actual_model = "mock"
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  KI Code Assistant - Chat with ki-core                       ║
║  Provider: {provider:<42} ║
║  Model:    {actual_model:<42} ║
║  Type 'help' for commands, 'quit' to exit                    ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    messages = []
    
    while True:
        try:
            user_input = input("You> ").strip()
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)
        
        if not user_input:
            continue
        
        if user_input.lower() == "quit":
            print("Goodbye!")
            break
        
        if user_input.lower() == "help":
            print("""
Commands:
  quit     - Exit
  clear    - Clear chat history
  history  - Show chat history
  help     - This message
""")
            continue
        
        if user_input.lower() == "clear":
            messages = []
            print("Chat history cleared.")
            continue
        
        if user_input.lower() == "history":
            if not messages:
                print("(empty)")
            else:
                for msg in messages:
                    role = msg.role.value if hasattr(msg.role, 'value') else msg.role
                    content = msg.content[:80]
                    print(f"{role}: {content}...")
            continue
        
        # Add user message
        messages.append(Message(role=Role.USER, content=user_input))
        
        # Get AI response
        request = ChatRequest(messages=messages)
        
        try:
            print("\nAssistant> ", end="", flush=True)
            
            # Stream response
            response_text = ""
            for event in client.chat_stream(request):
                if event.text:
                    print(event.text, end="", flush=True)
                    response_text += event.text
            
            print()  # Newline after response
            
            # Add assistant message to history
            messages.append(Message(role=Role.ASSISTANT, content=response_text))
            
        except Exception as e:
            print(f"\nERROR: {e}")
            print("(Make sure your provider is set up correctly)")
        
        print()


def run_chat_with_context(provider: str = "mock", project_root: str = None):
    """Interactive chat with project context awareness.
    
    Args:
        provider: LLM provider ('mock', 'ollama', 'openai')
        project_root: Project directory to analyze (default: current directory)
    """
    from kicli_code_assist.chat_session import ChatSession
    
    project_root = project_root or os.getcwd()
    
    # Load config and create session
    config = Config.from_env()
    session = ChatSession(project_root)
    
    # Create client
    try:
        client = create_client(config, provider)
    except Exception as e:
        print(f"ERROR: Failed to create {provider} client: {e}")
        sys.exit(1)
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  KI Code Assistant - Project-Aware Chat                      ║
║  Provider: {provider:<42} ║
║  Project:  {os.path.basename(project_root):<42} ║
║  Type 'help' for commands, 'quit' to exit                    ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    print("💡 Tip: Type 'load' to load project context for better answers")
    print()
    
    while True:
        try:
            user_input = input("You> ").strip()
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)
        
        if not user_input:
            continue
        
        if user_input.lower() == "quit":
            print("Goodbye!")
            break
        
        if user_input.lower() == "load":
            print("📊 Scanning project...")
            session.load_project_context()
            print(f"✅ {session.get_context_status()}")
            continue
        
        if user_input.lower() == "help":
            print("""
Commands:
  load     - Load project context for better answers
  status   - Show project context status
  quit     - Exit
  clear    - Clear chat history
  history  - Show chat history
  help     - This message
""")
            continue
        
        if user_input.lower() == "status":
            print(f"Context: {session.get_context_status()}")
            continue
        
        if user_input.lower() == "clear":
            session.clear_history()
            print("Chat history cleared.")
            continue
        
        if user_input.lower() == "history":
            if not session.messages:
                print("(empty)")
            else:
                for msg in session.messages:
                    role = msg.role.upper() if isinstance(msg.role, str) else msg.role
                    content = msg.content[:80]
                    print(f"{role}: {content}...")
            continue
        
        # Add user message to session
        session.add_message("user", user_input)
        
        # Get messages for API (includes system prompt with project context)
        api_messages = session.get_messages_for_api()
        
        # Convert to ki-core Message format
        messages = [
            Message(role=Role.SYSTEM if msg["role"] == "system" else 
                   Role.ASSISTANT if msg["role"] == "assistant" else 
                   Role.USER, content=msg["content"])
            for msg in api_messages
        ]
        
        request = ChatRequest(messages=messages)
        
        try:
            print("\nAssistant> ", end="", flush=True)
            
            # Stream response
            response_text = ""
            for event in client.chat_stream(request):
                if event.text:
                    print(event.text, end="", flush=True)
                    response_text += event.text
            
            print()  # Newline after response
            
            # Add assistant message to session
            session.add_message("assistant", response_text)
            
        except Exception as e:
            print(f"\nERROR: {e}")
            print("(Make sure your provider is set up correctly)")
        
        print()


if __name__ == "__main__":
    run_chat()