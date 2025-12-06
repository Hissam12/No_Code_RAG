import io
from typing import List
from fastapi import UploadFile
import os
import shutil
from langchain_community.document_loaders import PyPDFLoader

class IngestionService:
    def __init__(self, upload_dir: str = "pdfs"):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    async def process_file(self, file: UploadFile) -> str:
        """
        Saves the uploaded file and extracts text.
        Supports .txt and .pdf
        """
        file_path = os.path.join(self.upload_dir, file.filename)
        
        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Extract text based on extension
        if file.filename.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            return "\n".join([p.page_content for p in pages])
        else:
            # Assume text file
            with open(file_path, "r") as f:
                return f.read()

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Splits text into chunks.
        For MVP, we use a simple character-based sliding window.
        TODO: Implement true semantic chunking.
        """
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap
            
        return chunks
