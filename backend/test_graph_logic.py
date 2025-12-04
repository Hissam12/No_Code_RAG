import asyncio
import os
from dotenv import load_dotenv
from app.core.graph_builder import GraphBuilder

# Load environment variables
load_dotenv()

async def test_logic():
    print("Initializing GraphBuilder...")
    gb = GraphBuilder()
    
    print("\n--- Test 1: Extraction ---")
    # Read from sample.txt
    try:
        with open("../sample.txt", "r") as f:
            text = f.read()
    except FileNotFoundError:
        # Fallback if running from backend dir and file is in root
        with open("../sample.txt", "r") as f: 
             text = f.read()
    except Exception:
        # Fallback to hardcoded if file not found
        text = "GraphWeaver was created by Hissam in 2025. Hissam works at Google Deepmind."
        
    print(f"Input Text: {text[:100]}...")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: No OPENAI_API_KEY found. Please check your .env file.")
        return

    print("Extracting graph from text...")
    gb.extract_graph_from_text(text)
    
    graph_data = gb.visualize_graph()
    print(f"Graph Nodes: {len(graph_data['nodes'])}")
    print(f"Graph Edges: {len(graph_data['edges'])}")
    print("Nodes:", [n['label'] for n in graph_data['nodes']])
    
    print("\n--- Test 2: Querying ---")
    queries = [
        "Who created GraphWeaver?",
        "Where does Hissam work?",
        "What is ChromaDB?"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        answer = gb.query_graph(query)
        print(f"Answer: {answer}")

if __name__ == "__main__":
    asyncio.run(test_logic())
