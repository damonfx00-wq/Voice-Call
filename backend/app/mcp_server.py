"""MCP Server Implementation"""
import asyncio
import json
from typing import Any, Dict, List
from mcp.server import Server
from mcp.types import Tool, TextContent
from app.tools.csv_tools import CSVTools
from app.tools.rag_tool import RAGTool
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MCPServer:
    """MCP Server with CSV and RAG tools"""
    
    def __init__(self):
        self.server = Server("csv-rag-server")
        self.csv_tools = CSVTools(data_dir=os.getenv("CSV_DATA_DIR", "./data"))
        self.rag_tool = RAGTool(
            documents_dir=os.getenv("RAG_DOCUMENTS_DIR", "./data/documents"),
            vector_db_dir=os.getenv("VECTOR_DB_DIR", "./data/vector_db"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        )
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register MCP handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="read_csv",
                    description="Read data from a CSV file with optional filtering and column selection",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Name of the CSV file to read"
                            },
                            "filters": {
                                "type": "object",
                                "description": "Optional filters as column:value pairs",
                                "additionalProperties": True
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
                ),
                Tool(
                    name="write_csv",
                    description="Write data to a CSV file (overwrite, append, or update mode)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Name of the CSV file to write"
                            },
                            "data": {
                                "type": "array",
                                "items": {"type": "object"},
                                "description": "List of dictionaries to write"
                            },
                            "mode": {
                                "type": "string",
                                "enum": ["overwrite", "append", "update"],
                                "description": "Write mode: overwrite, append, or update",
                                "default": "overwrite"
                            }
                        },
                        "required": ["filename", "data"]
                    }
                ),
                Tool(
                    name="list_csv_files",
                    description="List all CSV files in the data directory with metadata",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="rag_ingest",
                    description="Ingest documents into the RAG vector database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional list of file paths to ingest (None = all files)"
                            }
                        }
                    }
                ),
                Tool(
                    name="rag_query",
                    description="Query the RAG system to retrieve relevant documents and context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of top results to return",
                                "default": 3
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="rag_clear",
                    description="Clear all documents from the RAG vector database",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Execute a tool"""
            
            result = None
            
            # CSV Tools
            if name == "read_csv":
                result = self.csv_tools.read_csv(
                    filename=arguments["filename"],
                    filters=arguments.get("filters"),
                    columns=arguments.get("columns"),
                    limit=arguments.get("limit")
                )
            
            elif name == "write_csv":
                result = self.csv_tools.write_csv(
                    filename=arguments["filename"],
                    data=arguments["data"],
                    mode=arguments.get("mode", "overwrite")
                )
            
            elif name == "list_csv_files":
                result = self.csv_tools.list_csv_files()
            
            # RAG Tools
            elif name == "rag_ingest":
                result = self.rag_tool.ingest_documents(
                    file_paths=arguments.get("file_paths")
                )
            
            elif name == "rag_query":
                result = self.rag_tool.query_with_context(
                    query=arguments["query"],
                    top_k=arguments.get("top_k", 3)
                )
            
            elif name == "rag_clear":
                result = self.rag_tool.clear_vector_store()
            
            else:
                result = {
                    "success": False,
                    "error": f"Unknown tool: {name}"
                }
            
            # Return result as TextContent
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
    
    async def run(self):
        """Run the MCP server"""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    server = MCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
