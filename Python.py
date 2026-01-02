import fitz  # PyMuPDF

# Input/output files
input_pdf = "input.pdf"   # replace with your PDF filename
output_pdf = "output.pdf"

# Open the input PDF
doc = fitz.open(input_pdf)
total_pages = len(doc)

# Create a new PDF for output
output_doc = fitz.open()

for i in range(0, total_pages, 2):
    # Get the first page of the pair
    page1 = doc[i]
    page2 = doc[i+1] if i+1 < total_pages else None

    # Get page dimensions
    rect1 = page1.rect
    w1, h1 = rect1.width, rect1.height
    w2, h2 = (page2.rect.width, page2.rect.height) if page2 else (0, 0)

    # Create a new page with combined dimensions
    combined_width = w1 + w2 if page2 else w1
    combined_height = max(h1, h2) if page2 else h1
    new_page = output_doc.new_page(width=combined_width, height=combined_height)

    # Insert first page at position (0, 0)
    new_page.show_pdf_page(fitz.Rect(0, 0, w1, h1), doc, i)
    
    # Insert second page next to it if it exists
    if page2:
        new_page.show_pdf_page(fitz.Rect(w1, 0, w1 + w2, h2), doc, i + 1)

# Save output
output_doc.save(output_pdf)
output_doc.close()
doc.close()

print(f"Merged PDF saved as {output_pdf}")
