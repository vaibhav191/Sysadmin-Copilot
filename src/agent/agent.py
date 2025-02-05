"""Agent module for handling LLM and tools setup."""

import os
import uuid
from typing import Tuple, Any, Literal, Dict
from langchain_anthropic import ChatAnthropic
from langgraph.graph import MessagesState, StateGraph
from langgraph.graph import START, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool
from ..tools.evaluator import command_evaluator
from ..tools.gmail import gmail_client
from datetime import datetime
# Initialize global variables
model_with_tool = None
tools_by_name: Dict = {}

# Tool definitions
@tool
def evaluator(command: str) -> str:
    """Evaluates command safety and executes via SSM if safe."""
    result = command_evaluator.evaluate_and_execute(command)
    return str(result)

@tool
def get_today_date() -> str:
    """Returns today's date in YYYY-MM-DD format."""
    print(f"Getting today's date")
    print(f"Today's date: {datetime.now().strftime('%Y-%m-%d')}")
    return datetime.now().strftime("%Y-%m-%d")

@tool
def email(task: str) -> str:
    """Executes Gmail-related tasks. Has access to 'create_gmail_draft', 'send_gmail_message', 'search_gmail', 'get_gmail_message', 'get_gmail_thread'.
        Send only one task at a time. Task must be granular. Example - Count all emails from 'john@doe.com' in the last 30 days.
    """
    try:
        print(f"\nAttempting Gmail task: {task}")
        result = gmail_client.execute_task(task)
        print(f"Gmail task result: {result.content}")
        return str(result)
    except Exception as e:
        error_msg = f"Gmail tool error: {str(e)}"
        print(error_msg)
        return error_msg

def llm_call(state: MessagesState):
    """LLM decides whether to call tools."""
    return {
        "messages": [
            model_with_tool.invoke(
                [
                    SystemMessage(content="""
You are a system administrator assistant, with 10+ years of experience in system administration.
Your job is to help the system administrator with user management tasks, with a focus on security best practices and efficient system administration.

You have access to the following tools:

evaluator: Executes commands on the Ubuntu EC2 instance for user management tasks including:
- Creating, modifying, and deleting user accounts
- Managing user permissions and sudo access
- Setting up user groups and group permissions
- Password management and security policies
- Managing SSH keys and access controls

email: Handles mail-related tasks (only when explicitly requested) such as:
- Sending system notifications
- User account credentials
- Security alerts
- System reports

get_today_date: Retrieves current date for:
- Log entries
- User account expiration
- Scheduled maintenance
- Audit trails

The copilot should:
- Draft/write your own email if you need to send an email
- You must provide an email address to send the email to a user
- Scan the instance for user details if you need to send an email to a user
- Verify all user inputs for security and validity
- Request additional information when necessary for task completion
- Confirm critical actions before execution
- Provide detailed feedback after task completion
- Follow Ubuntu security best practices
- Document all actions taken
- Handle errors gracefully with appropriate error messages
- When asked to query new emails, you must read all new unread emails to decide if any of them are related to what the user wants. Do not directly filter out any unread emails.
Example- When asked if we have any emails related to access control, you must check all unread emails
                                  and check if any of the emails are related to access control.

You MUST NOT USE EMAIL TOOLS UNLESS EXPLICITLY INSTRUCTED TO DO SO.
Do NOT EXECUTE ANY COMMANDS UNLESS EXPLICITLY INSTRUCTED TO DO SO.
MAKE SURE TO ASK USER FOR PERMISSION BEFORE EXECUTING WRITE COMMANDS OR COMMANDS THAT CHANGE THE SYSTEM.
You MUST CONFIRM THE EMAIL ADDRESS WITH THE USER BEFORE SENDING AN EMAIL.
                                
You do not have to ask for permissions for read-only commands.
                                  """)
                ] + state["messages"]
            )
        ]
    }

def tool_node(state: dict):
    """Perform the tool call."""
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        try:
            tool = tools_by_name.get(tool_call["name"])
            if not tool:
                raise ValueError(f"Tool '{tool_call['name']}' not found")
                
            observation = tool.invoke(tool_call["args"])
            result.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            result.append(ToolMessage(content=error_msg, tool_call_id=tool_call["id"]))
    return {"messages": result}

def should_continue(state: MessagesState) -> Literal["environment", "END"]:
    """Decide if we should continue the loop or stop."""
    messages = state["messages"]
    last_message = messages[-1]
    return "environment" if last_message.tool_calls else "END"

def create_agent() -> Tuple[Any, str]:
    """Create and configure the agent with tools and LLM.
    
    Returns:
        Tuple containing the configured agent and a unique thread ID
    """
    global model_with_tool, tools_by_name
    
    # Initialize LLM
    model = ChatAnthropic(
        model="claude-3-5-sonnet-latest",
        temperature=0.2,
        max_tokens=1024,
        timeout=None,
        max_retries=2,
    )
    
    # Setup tools
    tools = [evaluator, email, get_today_date]
    tools_by_name = {tool.name: tool for tool in tools}
    model_with_tool = model.bind_tools(tools)
    
    # Create agent workflow
    agent_builder = StateGraph(MessagesState)
    
    # Add nodes
    agent_builder.add_node("llm_call", llm_call)
    agent_builder.add_node("environment", tool_node)
    
    # Add edges
    agent_builder.add_edge(START, "llm_call")
    agent_builder.add_conditional_edges(
        "llm_call",
        should_continue,
        {"environment": "environment", "END": END}
    )
    agent_builder.add_edge("environment", "llm_call")
    
    # Compile agent
    memory = MemorySaver()
    agent = agent_builder.compile(checkpointer=memory)
    thread_id = str(uuid.uuid4())
    
    return agent, thread_id

def reset_agent() -> Tuple[Any, str]:
    """Reset the agent state and create a new conversation.
    
    Returns:
        Tuple containing a fresh agent instance and a new thread ID
    """
    return create_agent() 