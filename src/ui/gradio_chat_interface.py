"""Gradio-based chat interface for the SysPilot application."""

import gradio as gr
from typing import Any
from langchain_core.messages import HumanMessage
import os
from datetime import datetime
import json
from ..agent.agent import reset_agent

def create_chat_interface(agent: Any, thread_id: str):
    """Create and start the Gradio chat interface.
    
    Args:
        agent: The configured agent instance
        thread_id: Unique thread identifier
    """
    
    chat_history = []
    
    def save_chat_history(history):
        """Save chat history to a file with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("chat_logs", exist_ok=True)
        filename = f"chat_logs/chat_history_{timestamp}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"Chat Session: {timestamp}\n")
            f.write(f"Thread ID: {thread_id}\n")
            f.write("-" * 50 + "\n\n")
            for msg in history:
                f.write(f"{msg}\n")

    def new_chat():
        """Start a new chat session."""
        nonlocal agent, thread_id, chat_history
        # Save current chat history
        if chat_history:
            formatted_history = []
            for h in chat_history:
                formatted_history.append(f"User: {h['message']}")
                formatted_history.append(f"Assistant: {h['reply']}")
            save_chat_history(formatted_history)
        
        # Reset agent and get new thread ID
        agent, thread_id = reset_agent()
        chat_history = []
        return []  # Clear the chat interface

    def add_user_message(message: str, history):
        """Immediately add the user's message to chat history."""
        history.append({"role": "user", "content": message})
        return history, message

    def get_agent_response(message: str, history):
        """Get the agent's response and update chat history."""
        if message.lower() in ["exit", "quit", "bye", "end chat"]:
            # Save chat history before ending
            formatted_history = []
            for h in history:
                formatted_history.append(f"User: {h['content']}")
                formatted_history.append(f"Assistant: {h['content']}")
            save_chat_history(formatted_history)
            history.append({"role": "assistant", "content": "Chat ended and history saved. You can close this window."})
            return history, ""
        
        messages = [HumanMessage(message)]
        output = agent.invoke(
            {"messages": messages},
            config={"configurable": {"thread_id": thread_id}}
        )
        reply = output["messages"][-1].content if hasattr(output["messages"][-1], "content") else str(output["messages"][-1])
        
        # Store the full output data
        chat_history.append({
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "output": output,
            "reply": reply
        })
        
        # Add assistant's reply to history
        history.append({"role": "assistant", "content": reply})
        return history, ""

    # Create the interface using Blocks
    with gr.Blocks(
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="gray",
        )
    ) as interface:
        with gr.Row():
            gr.Markdown("# SysPilot AI Assistant")
            new_chat_btn = gr.Button(
                value="Reset",
                size="sm",
                variant="link",
                scale=0,
                min_width=0
            )
            
        gr.Markdown("Your AI system administration assistant (Type 'exit', 'quit', 'bye' or 'end chat' to end the conversation)")
        
        chatbot = gr.Chatbot(
            [],
            elem_id="chatbot",
            height=500,
            type="messages"  # Use new message format
        )
        
        txt = gr.Textbox(
            show_label=False,
            placeholder="Enter text and press enter",
            container=False
        )
        
        # Handle message submission - split into two steps
        msg_state = gr.State("")
        
        txt.submit(
            add_user_message,
            inputs=[txt, chatbot],
            outputs=[chatbot, msg_state],
            queue=False  # Disable queue to show message immediately
        ).then(
            get_agent_response,
            inputs=[msg_state, chatbot],
            outputs=[chatbot, txt],
            show_progress="minimal"
        )
        
        new_chat_btn.click(
            new_chat,
            None,
            chatbot,
            queue=False
        )
        
        # Add example queries
        gr.Examples(
            examples=[
                "What can you help me with?",
                "Check the status of my EC2 instances",
                "Show me my recent emails"
            ],
            inputs=txt
        )

    # Launch the interface
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True
    ) 