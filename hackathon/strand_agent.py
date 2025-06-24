#!/usr/bin/env python3
"""
Strand Agent with AWS Documentation MCP Server Integration

This agent uses the Strand framework to process tasks and has access to AWS documentation
through an MCP server.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, List, Optional

import boto3
import yaml
from strand import Strand, Task, TaskOutput
from mcp_client import MCPClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("strand-agent")

class AWSDocumentationAgent:
    """
    Strand agent with access to AWS documentation via MCP server.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the agent with configuration.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.strand = Strand(
            api_key=self.config.get("api_key", os.environ.get("OPENAI_API_KEY")),
            model=self.config.get("model", "gpt-4o"),
        )
        
        # Initialize MCP client for AWS documentation
        self.mcp_client = MCPClient()
        self.register_mcp_tools()
        
        # Output directory for results
        self.output_dir = self.config.get("output_dir", "output")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "model": "gpt-4o",
            "output_dir": "output",
            "tasks": [
                {
                    "name": "aws_documentation_search",
                    "description": "Search AWS documentation for specific topics",
                    "parameters": {
                        "search_phrase": "string",
                        "limit": "integer"
                    }
                }
            ]
        }
        
        if not config_path:
            logger.info("No config file provided, using defaults")
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {config_path}")
                return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return default_config
    
    def register_mcp_tools(self):
        """Register AWS documentation tools with the Strand instance."""
        
        @self.strand.tool
        def search_aws_documentation(search_phrase: str, limit: int = 10) -> List[Dict[str, Any]]:
            """
            Search AWS documentation using the MCP server.
            
            Args:
                search_phrase: The search phrase to use
                limit: Maximum number of results to return
                
            Returns:
                List of search results
            """
            try:
                results = self.mcp_client.call(
                    "awslabsaws_documentation_mcp_server___search_documentation",
                    {"search_phrase": search_phrase, "limit": limit}
                )
                return results
            except Exception as e:
                logger.error(f"Error searching AWS documentation: {e}")
                return []
        
        @self.strand.tool
        def read_aws_documentation(url: str, max_length: int = 5000, start_index: int = 0) -> str:
            """
            Read AWS documentation from a specific URL.
            
            Args:
                url: URL of the AWS documentation page
                max_length: Maximum content length to return
                start_index: Starting character index for pagination
                
            Returns:
                Documentation content in markdown format
            """
            try:
                content = self.mcp_client.call(
                    "awslabsaws_documentation_mcp_server___read_documentation",
                    {"url": url, "max_length": max_length, "start_index": start_index}
                )
                return content
            except Exception as e:
                logger.error(f"Error reading AWS documentation: {e}")
                return f"Error: {str(e)}"
        
        @self.strand.tool
        def get_aws_documentation_recommendations(url: str) -> List[Dict[str, Any]]:
            """
            Get recommendations for related AWS documentation.
            
            Args:
                url: URL of the AWS documentation page
                
            Returns:
                List of recommended pages
            """
            try:
                recommendations = self.mcp_client.call(
                    "awslabsaws_documentation_mcp_server___recommend",
                    {"url": url}
                )
                return recommendations
            except Exception as e:
                logger.error(f"Error getting AWS documentation recommendations: {e}")
                return []
    
    def process_task(self, task: Task) -> TaskOutput:
        """
        Process a task using the Strand framework.
        
        Args:
            task: The task to process
            
        Returns:
            Task output
        """
        logger.info(f"Processing task: {task.name}")
        
        # Add AWS documentation context to the task
        if "aws_service" in task.parameters:
            service = task.parameters["aws_service"]
            search_results = self.strand.tools.search_aws_documentation(
                search_phrase=f"{service} getting started",
                limit=5
            )
            
            if search_results and len(search_results) > 0:
                # Add the first result's content to the task context
                url = search_results[0].get("url")
                if url:
                    doc_content = self.strand.tools.read_aws_documentation(url=url)
                    task.context.append({
                        "type": "aws_documentation",
                        "content": doc_content,
                        "source": url
                    })
        
        # Process the task with Strand
        result = self.strand.process_task(task)
        
        # Save the result
        self._save_result(task.name, result)
        
        return result
    
    def _save_result(self, task_name: str, result: TaskOutput):
        """
        Save task result to output directory.
        
        Args:
            task_name: Name of the task
            result: Task output
        """
        output_path = os.path.join(self.output_dir, f"{task_name}_result.json")
        with open(output_path, 'w') as f:
            json.dump({
                "task": task_name,
                "output": result.output,
                "metadata": result.metadata
            }, f, indent=2)
        logger.info(f"Saved result to {output_path}")

def main():
    """Main entry point for the agent."""
    parser = argparse.ArgumentParser(description="Strand Agent with AWS Documentation Access")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--task", help="Task to run")
    parser.add_argument("--params", help="Task parameters as JSON string")
    args = parser.parse_args()
    
    agent = AWSDocumentationAgent(config_path=args.config)
    
    if args.task:
        task_params = {}
        if args.params:
            try:
                task_params = json.loads(args.params)
            except json.JSONDecodeError:
                logger.error("Invalid JSON in task parameters")
                sys.exit(1)
        
        task = Task(
            name=args.task,
            description=f"Running task {args.task}",
            parameters=task_params
        )
        
        result = agent.process_task(task)
        print(json.dumps({"output": result.output}, indent=2))
    else:
        # Run default task if none specified
        task = Task(
            name="aws_documentation_search",
            description="Search AWS documentation for CloudFormation",
            parameters={"search_phrase": "CloudFormation best practices"}
        )
        result = agent.process_task(task)
        print(json.dumps({"output": result.output}, indent=2))

if __name__ == "__main__":
    main()
