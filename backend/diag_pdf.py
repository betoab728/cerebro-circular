import sys
from pypdf import PdfReader

def diagnostic(file_path):
    try:
        reader = PdfReader(file_path)
        print(f"Total Pages: {len(reader.pages)}")
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            print(f"Page {i+1}: {len(text)} chars extracted.")
            if i < 2: # Show snippet of first two pages
                print(f"--- Snippet Page {i+1} ---")
                print(text[:500])
                print("-------------------------")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    path = r"C:\Users\ELIAS\Downloads\mina buenaventura- 2026.pdf"
    diagnostic(path)
