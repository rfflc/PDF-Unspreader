import fitz  # PyMuPDF

input_pdf = "output_vertical.pdf" # The long one we just made
output_pdf = "repaginated.pdf"

# Standard A4 dimensions in points
PAGE_WIDTH = 595
PAGE_HEIGHT = 842 
# How far "up" the script can look to find a blank spot to avoid cutting text
SEARCH_MARGIN = 40 

def find_best_cut(pix, target_y):
    """Looks for the closest blank row above the target_y to avoid cutting text."""
    samples = pix.samples
    width, height, ncomps = pix.width, pix.height, pix.n
    
    # Start at target_y and look upwards
    for y in range(int(target_y), int(target_y - SEARCH_MARGIN), -1):
        if y < 0: break
        row_start = y * width * ncomps
        # If the row is purely white (or very close to it)
        if all(c >= 252 for c in samples[row_start : row_start + width * ncomps]):
            return y
    return target_y # Fallback to exact cut if no white space found

# 1. Load the "Long" PDF
src_doc = fitz.open(input_pdf)
long_page = src_doc[0]
total_w = long_page.rect.width
total_h = long_page.rect.height

# Render the long page so we can "see" where the text is
# Note: For extremely long PDFs, render in chunks to save RAM
pix = long_page.get_pixmap(matrix=fitz.Matrix(1, 1)) 

output_doc = fitz.open()

current_top = 0
while current_top < total_h:
    remaining_h = total_h - current_top
    
    if remaining_h <= PAGE_HEIGHT:
        # Last page
        cut_h = remaining_h
    else:
        # Find a smart cut point within our target page height
        raw_cut = current_top + PAGE_HEIGHT
        smart_cut_px = find_best_cut(pix, raw_cut)
        cut_h = smart_cut_px - current_top

    # Create a new page with the source width and the calculated cut height
    new_page = output_doc.new_page(width=total_w, height=cut_h)
    
    # Define the "source window" (what we are looking at on the long page)
    # and the "target area" (the new page)
    clip_rect = fitz.Rect(0, current_top, total_w, current_top + cut_h)
    target_rect = fitz.Rect(0, 0, total_w, cut_h)
    
    new_page.show_pdf_page(target_rect, src_doc, 0, clip=clip_rect)
    
    current_top += cut_h

output_doc.save(output_pdf)
output_doc.close()
src_doc.close()

print(f"Repaginated PDF saved as {output_pdf}")