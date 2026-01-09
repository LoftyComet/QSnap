import os
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import models
from ..services import vision, export, llm

router = APIRouter()

UPLOAD_DIR = "static/uploads"
# Ensure directory exists as this module might be imported before main
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
def upload_paper(file: UploadFile = File(...), db: Session = Depends(get_db)):
    print(f"Received upload: {file.filename}")
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    db_paper = models.Paper(filename=file.filename, file_path=file_location)
    db.add(db_paper)
    db.commit()
    db.refresh(db_paper)
    print(f"Saved paper {db_paper.id}")
    return {"id": db_paper.id, "filename": db_paper.filename}

@router.get("/papers")
def list_papers(db: Session = Depends(get_db)):
    return db.query(models.Paper).order_by(models.Paper.created_at.desc()).all()

@router.get("/papers/{paper_id}")
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    # Return with sorted questions
    return {
        "paper": paper,
        "questions": sorted(paper.questions, key=lambda q: q.order_index)
    }

@router.delete("/papers/{paper_id}")
def delete_paper(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # 1. Delete associated physical files (crops)
    # We iterate a copy or just access the relationship
    for question in paper.questions:
         try:
             # question.image_path is relative like "static/uploads/..."
             if question.image_path and os.path.exists(question.image_path):
                 os.remove(question.image_path)
         except Exception as e:
             print(f"Error deleting question image {question.image_path}: {e}")
             
    # 2. Delete original paper file
    try:
        if paper.file_path and os.path.exists(paper.file_path):
            os.remove(paper.file_path)
    except Exception as e:
        print(f"Error deleting paper file {paper.file_path}: {e}")
    
    # 3. Delete database records
    # Because cascade is not strictly defined in models, we manually delete questions first
    for question in paper.questions:
        db.delete(question)
        
    db.delete(paper)
    db.commit()
    
    return {"message": "Paper deleted successfully"}

def background_solve_questions(question_ids: List[int], db: Session):
    for qid in question_ids:
        try:
            q = db.query(models.Question).filter(models.Question.id == qid).first()
            if q and q.ocr_text:
                # 1. Format and Check Integrity
                print(f"Formatting Q{qid}...")
                fmt_result = llm.format_and_check_question(q.ocr_text)
                
                q.ocr_text = fmt_result.get("formatted_text", q.ocr_text)
                q.is_incomplete = not fmt_result.get("is_complete", True)
                db.commit() # Save formatted text first
                
                # 2. Solve if complete
                if not q.is_incomplete:
                    print(f"Solving Q{qid}...")
                    # solution result is now a dict
                    sol_result = llm.solve_question(q.ocr_text)
                    
                    q.answer = sol_result.get("answer", "")
                    q.analysis = sol_result.get("analysis", "")
                    
                    # Backward compatibility / flag for frontend checking
                    q.solution_text = q.analysis 
                else:
                    print(f"Q{qid} marked incomplete")
                    # No solution text means frontend keeps waiting? 
                    # No, logic in frontend: if !solution -> "Generating..."
                    # So we MUST set solution_text to something, OR logic in frontend handles 'is_incomplete'
                    # We will rely on frontend reading 'is_incomplete' flag.
                    pass
                    
                db.commit()
        except Exception as e:
            print(f"Error solving question {qid}: {str(e)}")

@router.post("/process/{paper_id}")
def process_paper(paper_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    print(f"Processing paper {paper_id}")
    paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    if paper.is_processed:
        # If already processed, maybe retry logic or just return existing
        return {"status": "completed", "questions_found": len(paper.questions)}

    try:
        # Resolve absolute path to avoid cv2 issues with relative paths
        abs_file_path = os.path.abspath(paper.file_path)
        
        print(f"Vision processing: {abs_file_path}")
        
        # 1. OCR extracted from visual crops (Legacy/Hybrid)
        full_text = vision.extract_text_full_page(abs_file_path)
        print(f"Full Text Extracted: {len(full_text)} chars")
        
        # 2. Split text into questions using LLM
        question_texts = llm.split_text_into_questions(full_text)
        print(f"LLM Split into {len(question_texts)} questions")
        
        # 3. Create Question objects (Initially Unsolved)
        new_question_ids = []
        for idx, q_text in enumerate(question_texts):
            q = models.Question(
                paper_id=paper.id,
                image_path=paper.file_path, 
                bbox_json="[]", 
                ocr_text=q_text,
                solution_text="", # Empty initially
                order_index=idx + 1
            )
            db.add(q)
            db.commit()
            db.refresh(q)
            new_question_ids.append(q.id)
        
        paper.is_processed = True
        db.commit()

        # 4. Trigger Background Solving
        # We need a new Session for background task typically, but FastAPI dependency injection handles it if we pass it correctly?
        # Actually, passing 'db' to background task is risky if request closes. 
        # Better to pass IDs and let background task create new session? 
        # For simplicity in this small app, we'll try passing the function but we need to ensure DB session thread safety.
        # Ideally, we call a service function that gets its own DB session.
        # Let's use a simple wrapper that creates a new session.
        
        from ..database import SessionLocal
        def run_bg_solve(q_ids):
            bg_db = SessionLocal()
            try:
                background_solve_questions(q_ids, bg_db)
            finally:
                bg_db.close()

        background_tasks.add_task(run_bg_solve, new_question_ids)

        return {"status": "processing_started", "questions_found": len(question_texts)}
        
    except Exception as e:
        print(f"Error processing paper: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

        print(f"Error processing paper: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{paper_id}")
def export_paper(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    questions = sorted(paper.questions, key=lambda x: x.order_index)
    
    # Define output path
    output_filename = f"solutions_{paper.id}.docx"
    output_path = f"{UPLOAD_DIR}/{output_filename}"
    
    export.generate_word_doc(paper, questions, output_path)
    
    # Return URL to download
    return {"download_url": f"/static/uploads/{output_filename}"}
