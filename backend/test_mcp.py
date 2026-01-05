"""Test script for MCP Server and Agent"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.agent import IntelligentAgent
from app.tools.csv_tools import CSVTools
from app.tools.rag_tool import RAGTool
from dotenv import load_dotenv

load_dotenv()


def test_csv_tools():
    """Test CSV tools"""
    print("\n" + "="*60)
    print("Testing CSV Tools")
    print("="*60)
    
    csv_tools = CSVTools(data_dir="./data")
    
    # Test list files
    print("\n1. Listing CSV files:")
    result = csv_tools.list_csv_files()
    print(f"   Found {result.get('total_files', 0)} files")
    
    # Test read
    print("\n2. Reading employees.csv:")
    result = csv_tools.read_csv("employees.csv", limit=3)
    if result["success"]:
        print(f"   Read {result['rows']} rows")
        print(f"   Columns: {result['columns']}")
        print(f"   Sample data: {result['data'][0] if result['data'] else 'No data'}")
    
    # Test read with filter
    print("\n3. Reading with filter (department=Engineering):")
    result = csv_tools.read_csv(
        "employees.csv",
        filters={"department": "Engineering"}
    )
    if result["success"]:
        print(f"   Found {result['rows']} engineering employees")
    
    # Test write
    print("\n4. Writing new data:")
    new_data = [
        {"id": 11, "name": "Test User", "age": 25, "department": "IT", "salary": 55000}
    ]
    result = csv_tools.write_csv("test_output.csv", new_data)
    if result["success"]:
        print(f"   {result['message']}")


def test_rag_tool():
    """Test RAG tool"""
    print("\n" + "="*60)
    print("Testing RAG Tool")
    print("="*60)
    
    rag_tool = RAGTool(
        documents_dir="./data/documents",
        vector_db_dir="./data/vector_db"
    )
    
    # Test ingest
    print("\n1. Ingesting documents:")
    result = rag_tool.ingest_documents()
    if result["success"]:
        print(f"   {result['message']}")
        print(f"   Chunks created: {result['chunks_created']}")
    
    # Test query
    print("\n2. Querying: 'What are the company values?'")
    result = rag_tool.query_with_context("What are the company values?", top_k=2)
    if result["success"]:
        print(f"   Retrieved {result.get('message', '')}")
        print(f"   Context preview: {result['context'][:200]}...")


def test_agent():
    """Test intelligent agent"""
    print("\n" + "="*60)
    print("Testing Intelligent Agent")
    print("="*60)
    
    # Check if API key is set
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        print("\n⚠️  NVIDIA_API_KEY not set in .env file")
        print("   Skipping agent tests")
        return
    
    agent = IntelligentAgent()
    
    # Test 1: CSV query
    print("\n1. Agent Test - CSV Query:")
    print("   User: 'Show me all employees in the Engineering department'")
    response = agent.chat("Show me all employees in the Engineering department from employees.csv")
    print(f"   Agent: {response[:200]}...")
    
    # Test 2: RAG query
    print("\n2. Agent Test - RAG Query:")
    print("   User: 'What benefits does the company offer?'")
    agent.reset_conversation()
    response = agent.chat("What benefits does the company offer?")
    print(f"   Agent: {response[:200]}...")
    
    # Test 3: Mixed query
    print("\n3. Agent Test - Mixed Query:")
    print("   User: 'How many employees work in departments mentioned in the company docs?'")
    agent.reset_conversation()
    response = agent.chat("How many employees work in departments mentioned in the company docs?")
    print(f"   Agent: {response[:200]}...")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("MCP Server Test Suite")
    print("="*60)
    
    try:
        # Test CSV tools
        test_csv_tools()
        
        # Test RAG tool
        test_rag_tool()
        
        # Test agent (requires API key)
        test_agent()
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
