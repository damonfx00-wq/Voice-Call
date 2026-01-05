"""Intelligent Agent that uses MCP tools via NVIDIA API"""
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()


class IntelligentAgent:
    """Agent that decides which MCP tool to use based on user requests"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize agent with NVIDIA API
        
        Args:
            api_key: NVIDIA API key (or set NVIDIA_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY", "")
        
        # Initialize OpenAI client with NVIDIA base URL
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key
        )
        
        self.model = "openai/gpt-oss-120b"
        self.conversation_history = []
        
        # Tool definitions for function calling
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "read_csv",
                    "description": "Read data from a CSV file with optional filtering and column selection",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Name of the CSV file to read"
                            },
                            "filters": {
                                "type": "object",
                                "description": "Optional filters as column:value pairs"
                            },
                            "columns": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional list of columns to return"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of rows to return"
                            }
                        },
                        "required": ["filename"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_csv",
                    "description": "Write data to a CSV file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Name of the CSV file"
                            },
                            "data": {
                                "type": "array",
                                "items": {"type": "object"},
                                "description": "List of dictionaries to write"
                            },
                            "mode": {
                                "type": "string",
                                "enum": ["overwrite", "append", "update"],
                                "description": "Write mode"
                            }
                        },
                        "required": ["filename", "data"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_csv_files",
                    "description": "List all CSV files in the data directory",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "rag_query",
                    "description": "Query the RAG system to retrieve relevant information from documents",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of results to return"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "rag_ingest",
                    "description": "Ingest documents into the RAG system",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of file paths to ingest"
                            }
                        }
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool (this would call the MCP server in production)
        For now, we'll import and call directly
        """
        from app.tools.csv_tools import CSVTools
        from app.tools.rag_tool import RAGTool
        
        csv_tools = CSVTools(data_dir=os.getenv("CSV_DATA_DIR", "./data"))
        rag_tool = RAGTool(
            documents_dir=os.getenv("RAG_DOCUMENTS_DIR", "./data/documents"),
            vector_db_dir=os.getenv("VECTOR_DB_DIR", "./data/vector_db")
        )
        
        if tool_name == "read_csv":
            return csv_tools.read_csv(**arguments)
        elif tool_name == "write_csv":
            return csv_tools.write_csv(**arguments)
        elif tool_name == "list_csv_files":
            return csv_tools.list_csv_files()
        elif tool_name == "rag_query":
            return rag_tool.query_with_context(**arguments)
        elif tool_name == "rag_ingest":
            return rag_tool.ingest_documents(**arguments)
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
    
    def chat(self, user_message: str, stream: bool = False) -> str:
        """
        Process user message and decide which tools to use
        
        Args:
            user_message: User's message
            stream: Whether to stream the response
            
        Returns:
            Agent's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # System prompt
        system_message = {
            "role": "system",
            "content": """You are an intelligent assistant with access to CSV file operations and a RAG (Retrieval-Augmented Generation) system.

Your capabilities:
1. CSV Operations: Read, write, and list CSV files
2. RAG System: Query documents and retrieve relevant information

When a user asks a question:
- Use read_csv to read data from CSV files
- Use write_csv to create or update CSV files
- Use list_csv_files to see available CSV files
- Use rag_query to search through documents and retrieve relevant information
- Use rag_ingest to add new documents to the knowledge base

Always choose the most appropriate tool(s) for the task. You can use multiple tools in sequence if needed."""
        }
        
        messages = [system_message] + self.conversation_history
        
        try:
            # Make API call with function calling
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=4096,
                stream=stream
            )
            
            if stream:
                return self._handle_streaming_response(response)
            else:
                return self._handle_response(response)
                
        except Exception as e:
            error_msg = f"Error calling NVIDIA API: {str(e)}"
            self.conversation_history.append({
                "role": "assistant",
                "content": error_msg
            })
            return error_msg
    
    def _handle_response(self, response) -> str:
        """Handle non-streaming response"""
        assistant_message = response.choices[0].message
        
        # Check if tool calls are needed
        if assistant_message.tool_calls:
            # Execute tool calls
            tool_results = []
            
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                print(f"\n🔧 Executing tool: {tool_name}")
                print(f"   Arguments: {json.dumps(arguments, indent=2)}")
                
                result = self.execute_tool(tool_name, arguments)
                tool_results.append({
                    "tool": tool_name,
                    "result": result
                })
                
                # Add tool call and result to conversation
                self.conversation_history.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tool_call]
                })
                
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
            
            # Get final response with tool results
            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "Summarize the results"}] + self.conversation_history,
                temperature=0.7,
                max_tokens=4096
            )
            
            final_content = final_response.choices[0].message.content
            self.conversation_history.append({
                "role": "assistant",
                "content": final_content
            })
            
            return final_content
        else:
            # No tool calls, just return the response
            content = assistant_message.content
            self.conversation_history.append({
                "role": "assistant",
                "content": content
            })
            return content
    
    def _handle_streaming_response(self, response) -> str:
        """Handle streaming response"""
        full_response = ""
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                print(content, end="", flush=True)
        
        print()  # New line after streaming
        
        self.conversation_history.append({
            "role": "assistant",
            "content": full_response
        })
        
        return full_response
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
