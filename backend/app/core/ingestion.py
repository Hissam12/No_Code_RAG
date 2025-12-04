import io
from typing import List
from fastapi import UploadFile
from pypdf import PdfReader

class IngestionService:
    @staticmethod
    async def process_file(file: UploadFile) -> str:
        """Extracts text from an uploaded file (PDF or TXT)."""
        content = await file.read()
        
        if file.filename.endswith(".pdf"):
            return IngestionService._parse_pdf(content)
        else:
            # Assume text
            return content.decode("utf-8")

    @staticmethod
    def _parse_pdf(content: bytes) -> str:
        reader = PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

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
