"""Main entry point for the SysPilot application."""

import os
from dotenv import load_dotenv
from src.agent import create_agent
from src.ui.gradio_chat_interface import create_chat_interface

def main():
    """Initialize and start the application."""
    load_dotenv()
    
    # Initialize agent
    agent, thread_id = create_agent()
    print(f"Session ID: {thread_id}")
    
    # Start chat interface
    create_chat_interface(agent, thread_id)

if __name__ == "__main__":
    main()