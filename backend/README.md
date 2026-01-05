# MCP Server with Intelligent Agent

A FastAPI-based MCP (Model Context Protocol) server with CSV tools, RAG (Retrieval-Augmented Generation) capabilities, and an intelligent agent powered by NVIDIA's API.

## Features

- **CSV Tools**: Read, write, and list CSV files with filtering and column selection
- **RAG System**: Document ingestion, vector storage, and intelligent retrieval
- **Intelligent Agent**: LLM-powered agent that automatically selects the right tool for each task
- **MCP Protocol**: Standard protocol for tool discovery and execution
- **REST API**: FastAPI endpoints for all functionality

## Architecture

```
User Request → Intelligent Agent (NVIDIA API) → Tool Selection → MCP Server → Tools
                                                                              ├── CSV Tools
                                                                              ├── RAG Tool
                                                                              └── Results
```

## Installation

1. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env and add your NVIDIA_API_KEY
```

3. **Prepare data directories:**
```bash
mkdir -p data/documents data/vector_db
```

## Usage

### Starting the Server

```bash
# Development mode with auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Running Tests

```bash
python test_mcp.py
```

### Using the Agent (Chat Interface)

The agent automatically decides which tool to use based on your request:

**Example 1: CSV Query**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me all employees in the Engineering department"}'
```

**Example 2: RAG Query**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the company values?"}'
```

**Example 3: Mixed Query**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How many employees are in each department and what benefits do they get?"}'
```

### Direct Tool Access

#### CSV Operations

**List CSV files:**
```bash
curl http://localhost:8000/api/csv/list
```

**Read CSV:**
```bash
curl -X POST http://localhost:8000/api/csv/read \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "employees.csv",
    "filters": {"department": "Engineering"},
    "limit": 5
  }'
```

**Write CSV:**
```bash
curl -X POST http://localhost:8000/api/csv/write \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "new_data.csv",
    "data": [
      {"id": 1, "name": "John", "age": 30}
    ],
    "mode": "overwrite"
  }'
```

#### RAG Operations

**Ingest documents:**
```bash
curl -X POST http://localhost:8000/api/rag/ingest
```

**Query RAG:**
```bash
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What technologies does the engineering team use?",
    "top_k": 3
  }'
```

**Clear vector store:**
```bash
curl -X POST http://localhost:8000/api/rag/clear
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
backend/
├── app/
│   ├── agents/
│   │   ├── __init__.py
│   │   └── agent.py          # Intelligent agent with NVIDIA API
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── csv_tools.py      # CSV read/write operations
│   │   └── rag_tool.py       # RAG implementation
│   ├── mcp_server.py         # MCP protocol server
│   └── __init__.py
├── data/
│   ├── documents/            # Documents for RAG
│   ├── vector_db/            # ChromaDB vector store
│   └── *.csv                 # CSV files
├── main.py                   # FastAPI application
├── test_mcp.py              # Test suite
├── requirements.txt          # Dependencies
└── .env                      # Environment variables
```

## Environment Variables

```bash
# NVIDIA API Key (required for agent)
NVIDIA_API_KEY=your_nvidia_api_key

# Optional configurations
CSV_DATA_DIR=./data
RAG_DOCUMENTS_DIR=./data/documents
VECTOR_DB_DIR=./data/vector_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## How the Agent Works

1. **User sends a message** to the agent
2. **Agent analyzes** the request using NVIDIA's LLM
3. **Agent decides** which tool(s) to use via function calling
4. **Tools execute** the requested operations
5. **Agent synthesizes** the results into a natural language response

The agent can:
- Use multiple tools in sequence
- Combine data from different sources
- Handle complex multi-step queries
- Provide context-aware responses

## Example Workflows

### Workflow 1: Data Analysis
```
User: "Show me the average salary by department"
Agent: Uses read_csv → Analyzes data → Returns formatted results
```

### Workflow 2: Knowledge Retrieval
```
User: "What benefits does the company offer?"
Agent: Uses rag_query → Retrieves relevant docs → Summarizes benefits
```

### Workflow 3: Combined Query
```
User: "List engineering employees and tell me about the engineering department"
Agent: Uses read_csv + rag_query → Combines results → Provides comprehensive answer
```

## Troubleshooting

**Issue: ModuleNotFoundError**
```bash
# Make sure you're in the backend directory
cd backend
pip install -r requirements.txt
```

**Issue: NVIDIA API errors**
```bash
# Check your API key in .env
echo $NVIDIA_API_KEY

# Verify the key is valid at https://build.nvidia.com/
```

**Issue: ChromaDB errors**
```bash
# Clear and reinitialize vector store
rm -rf data/vector_db
python test_mcp.py
```

## License

MIT License
