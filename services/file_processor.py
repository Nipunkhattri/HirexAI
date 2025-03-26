from fastapi import HTTPException
import PyPDF2
import io

class FileProcessor:
    @staticmethod
    async def extract_text_from_pdf(file: bytes) -> str:
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file))
            return " ".join(page.extract_text() for page in pdf_reader.pages)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error processing PDF: {str(e)}"
            )