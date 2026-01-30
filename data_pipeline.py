"""
DATA INGESTION PIPELINE
Processes customer data and creates vector knowledge bases
"""

import os
import json
import hashlib
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import re

@dataclass
class DataSource:
    """Represents a single data source"""
    source_id: str
    source_type: str  # 'document', 'database', 'api', 'manual_text'
    content: str
    metadata: Dict
    
    def to_dict(self) -> Dict:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "content_hash": hashlib.sha256(self.content.encode()).hexdigest(),
            "content_length": len(self.content),
            "metadata": self.metadata
        }


class DataProcessor:
    """Processes and chunks data for embedding"""
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) <= chunk_size:
            return [text]
        
        start = 0
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                chunk = text[start:end]
                last_period = chunk.rfind('. ')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size * 0.5:  # Only break if we're past halfway
                    end = start + break_point + 1
            
            chunks.append(text[start:end].strip())
            start = end - overlap if end < len(text) else end
        
        return chunks
    
    @staticmethod
    def extract_metadata(content: str, source_type: str) -> Dict:
        """Extract relevant metadata from content"""
        metadata = {
            "char_count": len(content),
            "word_count": len(content.split()),
            "source_type": source_type
        }
        
        # Extract entities (simple version - can be enhanced with NER)
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
        
        if emails:
            metadata["contains_emails"] = True
            metadata["email_count"] = len(emails)
        
        if urls:
            metadata["contains_urls"] = True
            metadata["url_count"] = len(urls)
        
        return metadata


class VectorKnowledgeBase:
    """
    Manages the vector knowledge base for an agent
    Uses a simple in-memory structure (can be upgraded to Pinecone/Weaviate/etc)
    """
    
    def __init__(self, agent_id: str, storage_path: str = "/tmp/knowledge_bases"):
        self.agent_id = agent_id
        self.storage_path = Path(storage_path) / agent_id
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.chunks: List[Dict] = []
        self.sources: List[DataSource] = []
        self.embeddings: List[List[float]] = []  # Placeholder for actual embeddings
    
    def add_source(self, source: DataSource, chunk_size: int = 1000):
        """Add a data source and process it into chunks"""
        self.sources.append(source)
        
        # Chunk the content
        chunks = DataProcessor.chunk_text(source.content, chunk_size=chunk_size)
        
        # Store chunks with metadata
        for i, chunk in enumerate(chunks):
            chunk_id = f"{source.source_id}_chunk_{i}"
            chunk_data = {
                "chunk_id": chunk_id,
                "source_id": source.source_id,
                "content": chunk,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "metadata": source.metadata
            }
            self.chunks.append(chunk_data)
            
            # In production, generate actual embeddings here
            # For now, using placeholder
            self.embeddings.append([0.0] * 768)  # Typical embedding dimension
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for relevant chunks (simplified version)
        In production, use actual vector similarity search
        """
        # Simple keyword matching for demo
        query_lower = query.lower()
        scored_chunks = []
        
        for chunk in self.chunks:
            content_lower = chunk["content"].lower()
            score = sum(1 for word in query_lower.split() if word in content_lower)
            if score > 0:
                scored_chunks.append((score, chunk))
        
        # Sort by score and return top_k
        scored_chunks.sort(reverse=True, key=lambda x: x[0])
        return [chunk for score, chunk in scored_chunks[:top_k]]
    
    def save(self):
        """Persist knowledge base to disk"""
        kb_data = {
            "agent_id": self.agent_id,
            "sources": [s.to_dict() for s in self.sources],
            "chunks": self.chunks,
            "total_chunks": len(self.chunks),
            "total_sources": len(self.sources)
        }
        
        kb_path = self.storage_path / "knowledge_base.json"
        with open(kb_path, 'w') as f:
            json.dump(kb_data, f, indent=2)
        
        return kb_path
    
    def load(self):
        """Load knowledge base from disk"""
        kb_path = self.storage_path / "knowledge_base.json"
        if not kb_path.exists():
            raise FileNotFoundError(f"Knowledge base not found at {kb_path}")
        
        with open(kb_path, 'r') as f:
            kb_data = json.load(f)
        
        self.chunks = kb_data.get("chunks", [])
        return kb_data
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics"""
        return {
            "agent_id": self.agent_id,
            "total_sources": len(self.sources),
            "total_chunks": len(self.chunks),
            "total_characters": sum(len(chunk["content"]) for chunk in self.chunks),
            "source_types": list(set(s.source_type for s in self.sources))
        }


class DataIngestionPipeline:
    """
    Main pipeline for ingesting customer data
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.kb = VectorKnowledgeBase(agent_id)
        self.ingestion_log: List[Dict] = []
    
    def ingest_text(self, text: str, source_name: str = "manual_input") -> str:
        """Ingest plain text"""
        source_id = f"text_{hashlib.md5(text.encode()).hexdigest()[:8]}"
        
        metadata = DataProcessor.extract_metadata(text, "manual_text")
        metadata["source_name"] = source_name
        
        source = DataSource(
            source_id=source_id,
            source_type="manual_text",
            content=text,
            metadata=metadata
        )
        
        self.kb.add_source(source)
        self._log_ingestion(source_id, "manual_text", "success")
        
        return source_id
    
    def ingest_file(self, filepath: str) -> str:
        """Ingest a file (txt, md, json, etc.)"""
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Read file content
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        source_id = f"file_{path.stem}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
        
        metadata = DataProcessor.extract_metadata(content, "document")
        metadata.update({
            "filename": path.name,
            "file_extension": path.suffix,
            "file_size": len(content)
        })
        
        source = DataSource(
            source_id=source_id,
            source_type="document",
            content=content,
            metadata=metadata
        )
        
        self.kb.add_source(source)
        self._log_ingestion(source_id, "document", "success", {"filename": path.name})
        
        return source_id
    
    def ingest_api_data(self, data: Dict, api_name: str) -> str:
        """Ingest data from API response"""
        # Convert dict to searchable text
        content = json.dumps(data, indent=2)
        source_id = f"api_{api_name}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
        
        metadata = DataProcessor.extract_metadata(content, "api")
        metadata.update({
            "api_name": api_name,
            "data_keys": list(data.keys())
        })
        
        source = DataSource(
            source_id=source_id,
            source_type="api",
            content=content,
            metadata=metadata
        )
        
        self.kb.add_source(source)
        self._log_ingestion(source_id, "api", "success", {"api_name": api_name})
        
        return source_id
    
    def ingest_directory(self, directory_path: str, extensions: Optional[List[str]] = None) -> List[str]:
        """Ingest all compatible files from a directory"""
        if extensions is None:
            extensions = ['.txt', '.md', '.json', '.csv']
        
        dir_path = Path(directory_path)
        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {directory_path}")
        
        ingested_ids = []
        
        for ext in extensions:
            for file_path in dir_path.rglob(f"*{ext}"):
                try:
                    source_id = self.ingest_file(str(file_path))
                    ingested_ids.append(source_id)
                except Exception as e:
                    self._log_ingestion(str(file_path), "document", "failed", {"error": str(e)})
        
        return ingested_ids
    
    def finalize(self) -> Dict:
        """Finalize the ingestion and save knowledge base"""
        kb_path = self.kb.save()
        stats = self.kb.get_stats()
        
        summary = {
            "agent_id": self.agent_id,
            "knowledge_base_path": str(kb_path),
            "stats": stats,
            "ingestion_log": self.ingestion_log
        }
        
        # Save summary
        summary_path = self.kb.storage_path / "ingestion_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary
    
    def _log_ingestion(self, source_id: str, source_type: str, status: str, extra: Optional[Dict] = None):
        """Log ingestion event"""
        log_entry = {
            "source_id": source_id,
            "source_type": source_type,
            "status": status
        }
        
        if extra:
            log_entry.update(extra)
        
        self.ingestion_log.append(log_entry)


# Example usage
if __name__ == "__main__":
    # Create pipeline for an agent
    pipeline = DataIngestionPipeline(agent_id="agent_123")
    
    # Ingest various data sources
    pipeline.ingest_text(
        """
        Our company specializes in cloud infrastructure automation.
        We serve enterprise clients in finance, healthcare, and retail.
        Our core products include SecureCloud Pro and DataSync Enterprise.
        """,
        source_name="company_overview"
    )
    
    pipeline.ingest_text(
        """
        Q: What is our refund policy?
        A: We offer 30-day money-back guarantee on all products.
        
        Q: Do you offer enterprise support?
        A: Yes, 24/7 support is included with enterprise plans.
        """,
        source_name="faq"
    )
    
    # Finalize and get summary
    summary = pipeline.finalize()
    
    print("=== INGESTION COMPLETE ===")
    print(json.dumps(summary, indent=2))
    
    # Test search
    results = pipeline.kb.search("refund policy", top_k=3)
    print("\n=== SEARCH TEST: 'refund policy' ===")
    for result in results:
        print(f"\n{result['chunk_id']}:")
        print(result['content'][:200] + "...")
