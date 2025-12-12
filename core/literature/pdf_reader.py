import pypdf
import os
from typing import List

def extract_text_from_pdf(filepath: str) -> str:
    """
    Extracts text from a PDF file using pypdf.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"PDF file not found: {filepath}")

    text = ""
    try:
        reader = pypdf.PdfReader(filepath)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF {filepath}: {e}")
        return ""
    
    return text
