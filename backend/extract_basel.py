import pypdf
import os
import re
import json

pdf_path = "static/reglamento lgirs.pdf"
reader = pypdf.PdfReader(pdf_path)

catalog = []
# Annex VIII (List A) and Annex IX (List B)
# Basel codes usually follow Axxxx or Bxxxx format.
# Some might be Yx.
# Let's search from page 20 to the end just in case.
for i in range(18, len(reader.pages)):
    text = reader.pages[i].extract_text()
    
    # Simple regex for codes starting with A, B or Y
    # Codes like A1010, B3010, Y46
    # Pattern: Code [Optional newline/space] Description
    # But often the description follows immediately.
    
    # Try to find all codes
    matches = re.finditer(r'([ABY]\d{1,4})\s+([\s\S]+?)(?=[ABY]\d{1,4}|$)', text)
    for match in matches:
        code = match.group(1).strip()
        description = match.group(2).strip()
        # Clean up description (remove excess whitespace and newlines)
        description = re.sub(r'\s+', ' ', description)
        
        # Filter out false positives (too short descriptions or non-waste codes)
        if len(description) > 5:
            catalog.append({"codigo": code, "descripcion": description})

# Deduplicate
unique_catalog = []
seen_codes = set()
for item in catalog:
    if item["codigo"] not in seen_codes:
        unique_catalog.append(item)
        seen_codes.add(item["codigo"])

with open("backend/basel_catalog.json", "w", encoding="utf-8") as f:
    json.dump(unique_catalog, f, ensure_ascii=False, indent=2)

print(f"Extracted {len(unique_catalog)} codes to backend/basel_catalog.json")
