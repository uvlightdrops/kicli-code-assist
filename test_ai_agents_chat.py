#!/usr/bin/env python3
"""Test mode: Ollama and OpenAI chat with each other in real-time.

Demonstrates:
1. Two independent LLM provider threads
2. Real-time message exchange
3. Streaming responses displayed together
"""

import asyncio
import logging
from typing import Optional, Callable
from dataclasses import dataclass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ai-agents-chat")

# Add parent to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from kicli_code_assist.llm_integration import AsyncLLMIntegration
from kicli_code_assist.logging_integration import get_llm_logger


@dataclass
class AgentMessage:
    agent: str  # "Ollama" or "OpenAI"
    message: str
    full_response: str = ""
    chunks: list[str] = None
    
    def __post_init__(self):
        if self.chunks is None:
            self.chunks = []


class AIAgentsChat:
    """Two AI agents discussing a topic."""
    
    def __init__(self):
        self.integration = AsyncLLMIntegration()
        self.conversation_history = []
        
    async def agent_respond(
        self,
        agent_name: str,
        prompt: str,
        previous_messages: list[dict],
    ) -> AgentMessage:
        """Get response from one agent.
        
        Args:
            agent_name: "Ollama" or "OpenAI"
            prompt: The topic/question
            previous_messages: Chat history for context
            
        Returns:
            AgentMessage with agent response
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🤖 {agent_name} Agent Thinking...")
        logger.info(f"{'='*70}")
        
        # Build context from conversation
        system_prompt = f"""You are a helpful AI assistant named {agent_name}. 
You are discussing this topic with another AI.
Be concise (2-3 sentences), insightful, and build on previous points.
Use a friendly, collaborative tone."""
        
        # Add conversation history for context
        messages = previous_messages + [
            {"role": "user", "content": prompt}
        ]
        
        agent_message = AgentMessage(agent=agent_name, message=prompt)
        chunks_received = 0
        
        async def on_chunk(chunk: str):
            nonlocal chunks_received
            chunks_received += 1
            agent_message.chunks.append(chunk)
            agent_message.full_response += chunk
            
            # Display streaming in real-time
            print(f"  [{agent_name:8}] {chunk}", end="", flush=True)
        
        try:
            # Stream the response
            response = await self.integration.stream(
                messages=messages,
                system_prompt=system_prompt,
                on_chunk=on_chunk
            )
            
            print()  # Newline after streaming
            agent_message.full_response = response
            logger.info(f"✅ {agent_name} response complete ({chunks_received} chunks)")
            
            return agent_message
            
        except Exception as e:
            logger.error(f"❌ {agent_name} failed: {e}")
            agent_message.full_response = f"[Error: {e}]"
            return agent_message
    
    async def debate(self, topic: str, rounds: int = 3):
        """Run a debate between two AI agents.
        
        Args:
            topic: The topic to discuss
            rounds: Number of back-and-forth exchanges
        """
        logger.info("\n" + "="*70)
        logger.info(f"🎭 AI AGENTS CHAT MODE - Topic: '{topic}'")
        logger.info("="*70)
        
        # Initial prompt from user
        user_prompt = f"Let's discuss this topic: {topic}\n\nWhat's your perspective?"
        messages = [{"role": "user", "content": user_prompt}]
        
        agents = ["Ollama (llama3.2)", "OpenAI (gpt-4o-mini)"]
        current_round = 0
        
        while current_round < rounds:
            current_round += 1
            logger.info(f"\n{'─'*70}")
            logger.info(f"📍 Round {current_round}/{rounds}")
            logger.info(f"{'─'*70}")
            
            for agent_name in agents:
                # Create prompt for this agent
                if current_round == 1:
                    agent_prompt = f"Discuss this topic: {topic}"
                else:
                    # Reference the other agent's previous point
                    other_agent = agents[1] if agents[0] == agent_name else agents[0]
                    agent_prompt = f"Respond to what {other_agent} said and add your perspective on: {topic}"
                
                # Get agent response
                agent_message = await self.agent_respond(
                    agent_name=agent_name,
                    prompt=agent_prompt,
                    previous_messages=messages
                )
                
                # Add to conversation
                messages.append({
                    "role": "assistant",
                    "content": agent_message.full_response
                })
                self.conversation_history.append(agent_message)
                
                # Small delay between agents
                await asyncio.sleep(0.5)
        
        # Summary
        logger.info(f"\n{'='*70}")
        logger.info("📊 CONVERSATION SUMMARY")
        logger.info(f"{'='*70}")
        
        for i, msg in enumerate(self.conversation_history, 1):
            preview = msg.full_response[:100].replace('\n', ' ') + "..."
            logger.info(f"{i}. {msg.agent}: {preview}")
        
        logger.info(f"\n✅ Debate complete! {len(self.conversation_history)} messages exchanged.")
        return self.conversation_history


async def run_demo():
    """Run a demo of two AIs discussing async/await patterns."""
    
    print("\n" + "🚀" * 35)
    print("🚀 Welcome to AI Agents Chat Mode! 🚀".center(70))
    print("🚀" * 35 + "\n")
    
    chat = AIAgentsChat()
    
    # Example 1: Async/Await Patterns
    topic1 = "What makes async/await patterns powerful in modern programming?"
    print(f"Topic 1: {topic1}\n")
    await chat.debate(topic1, rounds=2)
    
    # Small break between debates
    print("\n" + "─"*70 + "\n")
    await asyncio.sleep(1)
    
    # Example 2: WebUI Architecture
    topic2 = "How should a real-time chat WebUI be designed for scalability?"
    print(f"\nTopic 2: {topic2}\n")
    chat2 = AIAgentsChat()  # Fresh chat
    await chat2.debate(topic2, rounds=2)
    
    print("\n" + "🎉" * 35)
    print("🎉 Demo Complete! 🎉".center(70))
    print("🎉" * 35 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
        logger.info("\n✅ SUCCESS: Both OpenAI and Ollama are working perfectly!")
    except KeyboardInterrupt:
        logger.info("\n⚠️  Demo interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
