# GraphWeaver - Local Ollama Setup

## ✅ Ready to Use!

Your GraphWeaver application is configured to run entirely on local Ollama models.

### Quick Start

1. **Add PDFs** to process:
   ```bash
   cp your-file.pdf backend/data/pdfs/
   ```

2. **Start the app**:
   ```bash
   ./run.sh
   ```

3. **Access**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000

### Test Setup

Run the test script to verify everything works:
```bash
cd backend
python3 test_ollama_setup.py
```

### Configuration

- **LLM**: gpt-oss:20b (graph extraction, Q&A)
- **Embeddings**: qwen3-embedding:8b (vector search)
- **Vector DB**: ChromaDB (local storage)
- **PDF Folder**: `backend/data/pdfs/`

All settings in `backend/app/.env`
