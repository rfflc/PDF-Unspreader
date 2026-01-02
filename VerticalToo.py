import fitz  # PyMuPDF
import math

input_pdf = "output.pdf"
output_pdf = "output_vertical.pdf"

STANDARD_DPI = 150
SCALE = STANDARD_DPI / 72.0 

def detect_vertical_margins(pix, is_joining_top, is_joining_bottom):
    samples = pix.samples
    width, height, ncomps = pix.width, pix.height, pix.n
    
    non_white_rows = []
    # Using 252 to be very sure we catch any faint anti-aliasing
    for y in range(height):
        row_start = y * width * ncomps
        if not all(c >= 252 for c in samples[row_start : row_start + width * ncomps]):
            non_white_rows.append(y)
    
    if not non_white_rows:
        return None

    # SEAMLESS LOGIC:
    # 0 buffer for joining edges to eliminate the gap.
    # 2 buffer for start/end of document for safety.
    top = non_white_rows[0] if is_joining_top else max(0, non_white_rows[0] - 2)
    bottom = non_white_rows[-1] if is_joining_bottom else min(height, non_white_rows[-1] + 2)
    
    return top, bottom

doc = fitz.open(input_pdf)
total_pages = len(doc)
output_doc = fitz.open()

page_data = []
total_height = 0
master_width = doc[0].rect.width 

for i in range(total_pages):
    page = doc[i]
    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE))
    
    v_margins = detect_vertical_margins(pix, (i > 0), (i < total_pages - 1))
    
    if v_margins:
        top_px, bottom_px = v_margins
        top_pt = top_px / SCALE
        bottom_pt = bottom_px / SCALE
    else:
        top_pt, bottom_pt = 0, page.rect.height
    
    h_pt = bottom_pt - top_pt
    page_data.append({
        'page_num': i,
        'height': h_pt,
        'clip': fitz.Rect(0, top_pt, page.rect.width, bottom_pt)
    })
    total_height += h_pt

# We use a tiny overlap to trick the renderer into not showing a white seam.
# 0.2 points is less than 1/3rd of a pixel at 72dpi—invisible but effective.
overlap_correction = 0.2
final_height = total_height - (overlap_correction * (total_pages - 1))

continuous_page = output_doc.new_page(width=master_width, height=final_height)

current_y = 0
for i, data in enumerate(page_data):
    target_rect = fitz.Rect(0, current_y, master_width, current_y + data['height'])
    continuous_page.show_pdf_page(target_rect, doc, data['page_num'], clip=data['clip'])
    
    # Subtract the tiny overlap for the next starting position
    current_y += (data['height'] - overlap_correction)

output_doc.save(output_pdf)
output_doc.close()
doc.close()

print(f"Seamless vertical PDF (No side-cropping) saved as {output_pdf}")