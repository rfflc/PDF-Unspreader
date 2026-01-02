import fitz

def get_best_cut_y(page, current_top, target_bottom, search_margin=100):
    """
    Finds a gap between text blocks so we don't cut through a line.
    """
    # Get all text blocks on the page
    blocks = page.get_text("blocks")
    
    # We want to cut as close to target_bottom as possible, but moving UP
    # to find a gap if necessary.
    best_cut = target_bottom
    
    # Filter for blocks that actually straddle our intended cut line
    straddling_blocks = [b for b in blocks if b[1] < target_bottom and b[3] > (target_bottom - 5)]

    if straddling_blocks:
        # Find the highest (top-most) y-coordinate among blocks being cut
        # We cut just above the highest block that the line hits.
        highest_y = min(b[1] for b in straddling_blocks)
        
        # Safety check: Don't jump back TOO far.
        if highest_y > (target_bottom - search_margin):
            best_cut = highest_y - 2 # 2pt buffer for safety
            
    return best_cut

def smart_repaginate_a4(input_path, output_path):
    src_doc = fitz.open(input_path)
    src_page = src_doc[0]
    src_rect = src_page.rect
    
    A4_W = 595
    A4_H = 842
    
    # Calculate scale to fit original width into A4 width
    scale_factor = A4_W / src_rect.width
    # How much of the ORIGINAL height fits into one A4 page?
    ideal_src_chunk_h = A4_H / scale_factor
    
    output_doc = fitz.open()
    current_y_src = 0
    
    print(f"Repaginating with text-detection...")

    while current_y_src < src_rect.height:
        remaining_h = src_rect.height - current_y_src
        
        # If what's left fits on one page, just take it
        if remaining_h <= ideal_src_chunk_h:
            src_cut_h = remaining_h
        else:
            # Find a smart cut point on the original coordinate system
            target_y = current_y_src + ideal_src_chunk_h
            best_y = get_best_cut_y(src_page, current_y_src, target_y)
            src_cut_h = best_y - current_y_src

        # Create the A4 page
        # Note: If we cut early, the page will be slightly shorter than A4. 
        # Most PDF readers handle this fine, or we can force A4_H if you prefer.
        new_page = output_doc.new_page(width=A4_W, height=src_cut_h * scale_factor)
        
        clip_rect = fitz.Rect(0, current_y_src, src_rect.width, current_y_src + src_cut_h)
        target_rect = fitz.Rect(0, 0, A4_W, src_cut_h * scale_factor)
        
        new_page.show_pdf_page(target_rect, src_doc, 0, clip=clip_rect)
        
        current_y_src += src_cut_h

    output_doc.save(output_path)
    print(f"Done! No text should be cut in {output_path}")

smart_repaginate_a4("output_vertical.pdf", "repaginated_vertical.pdf")