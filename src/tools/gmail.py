"""Gmail tools module for email operations."""

import os
from pathlib import Path
from langchain_google_community.gmail.utils import (
    build_resource_service,
    get_gmail_credentials,
)
from langchain_google_community import GmailToolkit
from typing import List, Any, Dict, Union
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

class GmailClient:
    def __init__(self):
        try:
            # Check if credentials file exists
            creds_path = Path("credentials.json")
            if not creds_path.exists():
                raise FileNotFoundError(
                    "credentials.json not found. Please download OAuth client credentials "
                    "from Google Cloud Console and save as 'credentials.json' in the project root."
                )
            
            # Check if token exists, if not it will trigger OAuth flow
            token_path = Path("token.json")
            if not token_path.exists():
                print("\nNo token.json found. Starting OAuth authentication flow...")
                print("Please follow the instructions in your browser to authenticate.")
                
            self.credentials = get_gmail_credentials(
                token_file="token.json",
                scopes=["https://mail.google.com/"],
                client_secrets_file="credentials.json",
            )
            
            # Setup Gmail toolkit and tools
            self.api_resource = build_resource_service(credentials=self.credentials)
            self.toolkit = GmailToolkit(api_resource=self.api_resource)
            self.tools = self.toolkit.get_tools()
            self.tools_by_name = {tool.name: tool for tool in self.tools}
            # Initialize LLM for the agent
            llm = ChatAnthropic(
                model="claude-3-5-sonnet-latest",
                temperature=0.2,
                max_tokens=1024
            )
            
            # Create the agent
            self.agent = create_react_agent(
                llm,
                self.tools,
            )
            
            
            print("\nAvailable Gmail tools:")
            for tool in self.tools:
                print(f"- {tool.name}: {tool.description}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Gmail client: {str(e)}")
    
    def execute_task(self, task: str) -> Union[List[Any], Dict[str, str]]:
        """Execute a Gmail-related task using the ReAct agent.
        
        Args:
            task: Description of the task to perform
            
        Returns:
            Results from the task execution or error message
        """
        try:
            result = self.agent.stream({"messages":[("user", task)]}, stream_mode="values")
            return list(result)[-1]["messages"][-1]
        except Exception as e:
            return {"error": f"Gmail operation failed: {str(e)}"}

gmail_client = GmailClient() 