"""AWS tools module for executing commands on EC2 instances via SSM."""

import os
import time
import boto3
from typing import Dict, Any

class SSMClient:
    def __init__(self):
        # Required environment variables
        required_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "REGION_NAME", "INSTANCE_ID"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
            
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region_name = os.getenv("REGION_NAME")
        self.instance_id = os.getenv("INSTANCE_ID")
        
        try:
            self.session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name,
            )
            self.client = self.session.client('ssm')
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AWS SSM client: {str(e)}")
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a command on the EC2 instance via SSM.
        
        Args:
            command: The shell command to execute
            
        Returns:
            Dict containing the command output and status
        """
        print(f"\n[AWS Command Input] Executing: {command}")
        try:
            response = self.client.send_command(
                InstanceIds=[self.instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={'commands': [command]},
            )
            command_id = response['Command']['CommandId']
            print(f"[AWS] Command ID: {command_id}")
            
            # Polling logic with timeout
            max_attempts = 30
            for attempt in range(max_attempts):
                time.sleep(3)
                status = self.client.get_command_invocation(
                    CommandId=command_id,
                    InstanceId=self.instance_id
                )['Status']
                print(f"[AWS] Status (attempt {attempt + 1}/{max_attempts}): {status}")
                
                if status in ['Success', 'Failed', 'Cancelled', 'Delivery Timed Out', 
                            'Execution Timed Out', 'Undelivered', 'Terminated']:
                    break
            else:
                print("[AWS Error] Command timed out after 30 seconds")
                return {"error": "Command timed out after 30 seconds"}
                
            output = self.client.get_command_invocation(
                CommandId=command_id,
                InstanceId=self.instance_id
            )
            print(f"\n[AWS Command Output]\nStatus: {output.get('Status')}\nOutput:\n{output.get('StandardOutputContent', '')}")
            if output.get('StandardErrorContent'):
                print(f"Error Output:\n{output.get('StandardErrorContent')}")
            return output
            
        except Exception as e:
            error_msg = f"SSM Execution Error: {str(e)}"
            print(f"[AWS Error] {error_msg}")
            return {"error": error_msg}

ssm_client = SSMClient() 