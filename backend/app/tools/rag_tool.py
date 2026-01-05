"""RAG Agent Tool for MCP Server"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import chromadb


class RAGTool:
    """RAG (Retrieval-Augmented Generation) Tool"""
    
    def __init__(
        self,
        documents_dir: str = "./data/documents",
        vector_db_dir: str = "./data/vector_db",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        self.documents_dir = Path(documents_dir)
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        
        self.vector_db_dir = Path(vector_db_dir)
        self.vector_db_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize or load vector store
        self.vector_store = None
        self._load_or_create_vector_store()
    
    def _load_or_create_vector_store(self):
        """Load existing vector store or create new one"""
        try:
            # Try to load existing vector store
            self.vector_store = Chroma(
                persist_directory=str(self.vector_db_dir),
                embedding_function=self.embeddings,
                collection_name="rag_documents"
            )
        except Exception as e:
            # Create new vector store
            self.vector_store = Chroma(
                persist_directory=str(self.vector_db_dir),
                embedding_function=self.embeddings,
                collection_name="rag_documents"
            )
    
    def ingest_documents(self, file_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Ingest documents into the vector store
        
        Args:
            file_paths: List of file paths to ingest (None = all files in documents_dir)
            
        Returns:
            Dictionary with ingestion results
        """
        try:
            if file_paths is None:
                # Get all text files from documents directory
                file_paths = []
                for ext in ['*.txt', '*.md', '*.csv']:
                    file_paths.extend(self.documents_dir.glob(ext))
            else:
                file_paths = [Path(fp) for fp in file_paths]
            
            documents = []
            for file_path in file_paths:
                if not file_path.exists():
                    continue
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    documents.append(Document(
                        page_content=content,
                        metadata={"source": str(file_path.name)}
                    ))
            
            if not documents:
                return {
                    "success": False,
                    "error": "No documents found to ingest",
                    "documents_ingested": 0
                }
            
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len
            )
            splits = text_splitter.split_documents(documents)
            
            # Add to vector store
            self.vector_store.add_documents(splits)
            
            return {
                "success": True,
                "documents_ingested": len(documents),
                "chunks_created": len(splits),
                "message": f"Successfully ingested {len(documents)} documents"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "documents_ingested": 0
            }
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            Dictionary with retrieved documents
        """
        try:
            # Search vector store
            results = self.vector_store.similarity_search_with_score(
                query,
                k=top_k
            )
            
            # Format results
            retrieved_docs = []
            for doc, score in results:
                retrieved_docs.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                    "relevance_score": float(score)
                })
            
            return {
                "success": True,
                "query": query,
                "results_count": len(retrieved_docs),
                "documents": retrieved_docs
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "documents": []
            }
    
    def query_with_context(
        self,
        query: str,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Retrieve documents and format them as context for LLM
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            
        Returns:
            Dictionary with context and documents
        """
        try:
            retrieval_result = self.retrieve(query, top_k)
            
            if not retrieval_result["success"]:
                return retrieval_result
            
            # Build context string
            context_parts = []
            for i, doc in enumerate(retrieval_result["documents"], 1):
                context_parts.append(
                    f"[Document {i} - Source: {doc['source']}]\n{doc['content']}\n"
                )
            
            context = "\n".join(context_parts)
            
            return {
                "success": True,
                "query": query,
                "context": context,
                "documents": retrieval_result["documents"],
                "message": f"Retrieved {len(retrieval_result['documents'])} relevant documents"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "context": "",
                "documents": []
            }
    
    def clear_vector_store(self) -> Dict[str, Any]:
        """Clear all documents from vector store"""
        try:
            # Delete and recreate vector store
            import shutil
            if self.vector_db_dir.exists():
                shutil.rmtree(self.vector_db_dir)
            
            self._load_or_create_vector_store()
            
            return {
                "success": True,
                "message": "Vector store cleared successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
