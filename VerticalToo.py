import fitz  # PyMuPDF

# Input/output files
input_pdf = "output.pdf"   # replace with your PDF filename
output_pdf = "output_vertical.pdf"

# Standard DPI for normalization - all pages rendered at same resolution
STANDARD_DPI = 150
SCALE = STANDARD_DPI / 72.0  # Convert from PDF points to pixels

def detect_margins_pixmap(pix, crop_bottom_aggressive=False, crop_top_aggressive=False):
    """Detect white margins by analyzing pixmap pixels - very aggressive"""
    samples = pix.samples
    width = pix.width
    height = pix.height
    ncomps = pix.n
    
    # Find non-white rows and columns
    non_white_rows = []
    non_white_cols = []
    
    # Check rows
    for y in range(height):
        row_start = y * width * ncomps
        is_row_white = True
        for x in range(width):
            pixel_start = row_start + x * ncomps
            pixel = samples[pixel_start:pixel_start + ncomps]
            # Extremely strict: all channels must be >= 255 (pure white) to be considered white
            if not all(c >= 255 for c in pixel):
                is_row_white = False
                break
        if not is_row_white:
            non_white_rows.append(y)
    
    # Check columns
    for x in range(width):
        is_col_white = True
        for y in range(height):
            pixel_start = (y * width + x) * ncomps
            pixel = samples[pixel_start:pixel_start + ncomps]
            if not all(c >= 255 for c in pixel):
                is_col_white = False
                break
        if not is_col_white:
            non_white_cols.append(x)
    
    if len(non_white_rows) == 0 or len(non_white_cols) == 0:
        return None
    
    # Check if bottom edge has white pixels - moderate approach
    bottom_has_white = False
    if crop_bottom_aggressive and len(non_white_rows) > 0:
        last_content_row = non_white_rows[-1]
        # Check only the row immediately after content (very conservative)
        if last_content_row + 1 < height:
            y = last_content_row + 1
            row_start = y * width * ncomps
            all_white = True
            # Sample only middle portion to be safer
            sample_start = width // 4
            sample_end = 3 * width // 4
            for x in range(sample_start, sample_end):
                pixel_start = row_start + x * ncomps
                pixel = samples[pixel_start:pixel_start + ncomps]
                if not all(c >= 255 for c in pixel):
                    all_white = False
                    break
            if all_white:
                bottom_has_white = True
    
    # Check if top edge has white pixels - moderate approach
    top_has_white = False
    if crop_top_aggressive and len(non_white_rows) > 0:
        first_content_row = non_white_rows[0]
        # Check only the row immediately before content (very conservative)
        if first_content_row > 0:
            y = first_content_row - 1
            row_start = y * width * ncomps
            all_white = True
            # Sample only middle portion to be safer
            sample_start = width // 4
            sample_end = 3 * width // 4
            for x in range(sample_start, sample_end):
                pixel_start = row_start + x * ncomps
                pixel = samples[pixel_start:pixel_start + ncomps]
                if not all(c >= 255 for c in pixel):
                    all_white = False
                    break
            if all_white:
                top_has_white = True
    
    # Moderate cropping - only crop 1-2 pixels when we detect white, otherwise use small padding
    if crop_top_aggressive and top_has_white:
        top = max(0, non_white_rows[0] + 1)  # Crop only 1 pixel when white detected
    else:
        top = max(0, non_white_rows[0] - 1)  # Small padding to avoid cutting
    
    if crop_bottom_aggressive and bottom_has_white:
        bottom = min(height, non_white_rows[-1] - 1)  # Crop only 1 pixel when white detected
    else:
        bottom = min(height, non_white_rows[-1] + 2)  # Small padding to avoid cutting
    left = max(0, non_white_cols[0] - 1)
    right = min(width, non_white_cols[-1] + 1)
    
    return (left, top, right, bottom)

# Open the input PDF
doc = fitz.open(input_pdf)
total_pages = len(doc)

# Create a new PDF for output - ONE CONTINUOUS PAGE
output_doc = fitz.open()

# First pass: collect all page data and find common width
page_data = []
min_left = float('inf')
max_right = float('-inf')
total_height = 0

print("Analyzing pages and normalizing resolution...")
for i in range(0, total_pages, 2):
    page1 = doc[i]
    page2 = doc[i+1] if i+1 < total_pages else None
    
    # Render at standard DPI to normalize resolution
    mat = fitz.Matrix(SCALE, SCALE)
    pix1 = page1.get_pixmap(matrix=mat)
    pix2 = page2.get_pixmap(matrix=mat) if page2 else None
    
    # Detect margins - crop bottom aggressively for page1 (will join with page2)
    # Crop top aggressively for page2 (joins with page1)
    is_last_pair = (i + 1 >= total_pages)
    margins1 = detect_margins_pixmap(pix1, crop_bottom_aggressive=not is_last_pair, crop_top_aggressive=False)
    margins2 = detect_margins_pixmap(pix2, crop_bottom_aggressive=False, crop_top_aggressive=True) if pix2 else None
    
    if margins1 is None:
        margins1 = (0, 0, pix1.width, pix1.height)
    if margins2 is None and page2:
        margins2 = (0, 0, pix2.width, pix2.height)
    
    # Convert pixel coords back to PDF points
    left1, top1, right1, bottom1 = margins1
    w1_px = right1 - left1
    h1_px = bottom1 - top1
    w1_pt = w1_px / SCALE
    h1_pt = h1_px / SCALE
    left1_pt = left1 / SCALE
    right1_pt = right1 / SCALE
    
    min_left = min(min_left, left1_pt)
    max_right = max(max_right, right1_pt)
    
    page_data.append({
        'page_num': i,
        'left': left1_pt,
        'top': top1 / SCALE,
        'width': w1_pt,
        'height': h1_pt,
        'clip': fitz.Rect(left1_pt, top1 / SCALE, right1_pt, (top1 + h1_px) / SCALE)
    })
    total_height += h1_pt
    
    if page2 and margins2:
        left2, top2, right2, bottom2 = margins2
        w2_px = right2 - left2
        h2_px = bottom2 - top2
        w2_pt = w2_px / SCALE
        h2_pt = h2_px / SCALE
        left2_pt = left2 / SCALE
        right2_pt = right2 / SCALE
        
        min_left = min(min_left, left2_pt)
        max_right = max(max_right, right2_pt)
        
        page_data.append({
            'page_num': i + 1,
            'left': left2_pt,
            'top': top2 / SCALE,
            'width': w2_pt,
            'height': h2_pt,
            'clip': fitz.Rect(left2_pt, top2 / SCALE, right2_pt, (top2 + h2_px) / SCALE)
        })
        total_height += h2_pt

# Common width for all pages
common_width = max_right - min_left

# Create ONE continuous page
print(f"Creating continuous page: width={common_width:.1f}, height={total_height:.1f}")
continuous_page = output_doc.new_page(width=common_width, height=total_height)

# Stack all pages vertically on the continuous page
current_y = 0
for data in page_data:
    # Align all pages to same left edge
    aligned_clip = fitz.Rect(min_left, data['clip'].y0, min_left + common_width, data['clip'].y1)
    target_rect = fitz.Rect(0, current_y, common_width, current_y + data['height'])
    
    continuous_page.show_pdf_page(target_rect, doc, data['page_num'], clip=aligned_clip)
    current_y += data['height']

# Save output
output_doc.save(output_pdf)
output_doc.close()
doc.close()

print(f"Merged vertically split PDF saved as {output_pdf}")

