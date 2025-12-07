#!/usr/bin/env python3
"""
Quick test script to verify Ollama integration works correctly
"""
import os
import sys
from dotenv import load_dotenv

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), 'app', '.env'))

print("=" * 60)
print("Testing GraphWeaver Ollama Integration")
print("=" * 60)

# Test 1: LLM Service
print("\n1. Testing LLM Service (gpt-oss:20b)...")
try:
    from app.core.llm_service import LLMService, get_llm
    
    llm = get_llm()
    print(f"   ✓ LLM initialized: {llm}")
    
    # Test simple extraction
    service = LLMService()
    test_text = "Apple Inc. was founded by Steve Jobs in Cupertino, California."
    nodes, edges = service.extract_graph_data(test_text)
    
    print(f"   ✓ Extracted {len(nodes)} nodes and {len(edges)} edges")
    if nodes:
        print(f"   Sample node: {nodes[0].label} ({nodes[0].type})")
    if edges:
        print(f"   Sample edge: {edges[0].relation}")
        
except Exception as e:
    print(f"   ✗ LLM test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Embeddings
print("\n2. Testing Embeddings (qwen3-embedding:8b)...")
try:
    from app.core.vector_store import get_embeddings
    
    embeddings = get_embeddings()
    print(f"   ✓ Embeddings initialized: {embeddings}")
    
    # Test embedding generation
    test_embedding = embeddings.embed_query("Hello world")
    print(f"   ✓ Generated embedding with {len(test_embedding)} dimensions")
    
except Exception as e:
    print(f"   ✗ Embeddings test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Vector Store
print("\n3. Testing ChromaDB Vector Store...")
try:
    from app.core.vector_store import VectorStore
    
    vs = VectorStore(collection_name="test_collection")
    print(f"   ✓ Vector store initialized")
    
    # Add test documents
    vs.add_documents(
        documents=["Test document 1", "Test document 2"],
        metadatas=[{"source": "test1"}, {"source": "test2"}],
        ids=["doc1", "doc2"]
    )
    print(f"   ✓ Added 2 test documents")
    print(f"   ✓ Total documents in collection: {vs.get_document_count()}")
    
    # Test query
    results = vs.query_similar("Test document", n_results=1)
    print(f"   ✓ Query returned {len(results)} results")
    
    # Cleanup
    vs.delete_collection()
    print(f"   ✓ Test collection cleaned up")
    
except Exception as e:
    print(f"   ✗ Vector store test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✓ All tests completed!")
print("=" * 60)
print(f"\nConfiguration:")
print(f"  LLM Model: {os.getenv('OLLAMA_MODEL')}")
print(f"  Embedding Model: {os.getenv('OLLAMA_EMBEDDING_MODEL')}")
print(f"  Ollama URL: {os.getenv('OLLAMA_BASE_URL')}")
print(f"  PDF Upload Dir: backend/data/pdfs/")
print(f"  ChromaDB Dir: backend/data/chroma_db/")
print()
