from docx import Document
from docx.shared import Inches
import os

def generate_word_doc(paper, questions, output_path):
    document = Document()
    
    document.add_heading(f'Solutions: {paper.filename}', 0)
    
    for idx, q in enumerate(questions):
        document.add_heading(f'Question {idx + 1}', level=1)
        
        # Add Question Text (OCR)
        if q.ocr_text:
            document.add_paragraph("Question Text:", style='Intense Quote')
            document.add_paragraph(q.ocr_text)
            
        # Add Image Crop
        # Depending on path structure, might need to resolve absolute path
        # q.image_path is "static/uploads/..." relative to root
        # We need absolute path for python-docx
        abs_image_path = os.path.abspath(q.image_path)
        if os.path.exists(abs_image_path):
            try:
                document.add_picture(abs_image_path, width=Inches(4.0))
            except Exception:
                document.add_paragraph("[Image could not be added]")
        
        # Add Solution
        document.add_heading('Solution', level=2)
        document.add_paragraph(q.solution_text if q.solution_text else "[No solution generated]")
        
        document.add_page_break()
        
    document.save(output_path)
    return output_path
