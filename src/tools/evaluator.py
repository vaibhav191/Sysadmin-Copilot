"""Command evaluator module for safely executing system commands."""

import re
from typing import Dict, Any
from .aws import ssm_client

class CommandEvaluator:
    def __init__(self):
        self.unsafe_patterns = [
            r'\bwget\b', r'\bcurl\b', r'\bunset\b',
            # Add more unsafe patterns here
        ]
    
    def evaluate_and_execute(self, command: str) -> Dict[str, Any]:
        """Evaluate command safety and execute if safe.
        
        Args:
            command: The shell command to evaluate and execute
            
        Returns:
            Dict containing execution result or error message
        """
        # Check for unsafe patterns
        for pattern in self.unsafe_patterns:
            if re.search(pattern, command):
                return {
                    "error": f"Command blocked: Unsafe pattern '{pattern}' detected. Modify your command."
                }
        
        # If safe, execute via SSM
        return ssm_client.execute_command(command)

command_evaluator = CommandEvaluator() 