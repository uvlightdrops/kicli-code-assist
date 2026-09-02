#!/usr/bin/env python3
"""
Example: Using ki-core with kicli-code-assist

This demonstrates how to integrate ki-core AI client abstractions
with the code assistant.
"""

from ki_core.core.models import ChatRequest, Message, Role
from ki_core.adapters.mock.client import MockAIClient


def main():
    """Demonstrate ki-core integration."""
    # Use the mock client (no API key required)
    client = MockAIClient()

    # Create a chat request
    messages = [
        Message(role=Role.SYSTEM, content="You are a helpful code assistant."),
        Message(role=Role.USER, content="Write a Python function to check if a number is prime."),
    ]

    request = ChatRequest(
        messages=messages,
        model="mock",
        temperature=0.7,
        metadata={"source": "kicli-assist"},
    )

    # Non-streaming response
    print("=== Non-Streaming Response ===")
    response = client.chat(request)
    print(f"Role: {response.message.role}")
    print(f"Content: {response.message.content}")
    print(f"Model: {response.model}")
    print()

    # Streaming response
    print("=== Streaming Response ===")
    for event in client.chat_stream(request):
        if event.text:
            print(event.text, end="", flush=True)
    print("\n")


if __name__ == "__main__":
    main()
