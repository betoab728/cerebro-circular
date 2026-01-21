import pypdf
import os

pdf_path = "static/reglamento lgirs.pdf"
if not os.path.exists(pdf_path):
    print(f"Error: {pdf_path} not found")
else:
    reader = pypdf.PdfReader(pdf_path)
    num_pages = len(reader.pages)
    print(f"Total pages: {num_pages}")
    
    # Start from page 23 (index 22) or 24 (index 23) as per user suggestion
    for i in range(22, min(30, num_pages)):
        print(f"\n--- PAGE {i+1} ---\n")
        text = reader.pages[i].extract_text()
        print(text[:2000])
