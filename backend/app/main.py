import os
import shutil
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException

# Load environment variables from .env file
load_dotenv()

from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from .services import vision, llm, export

from .database import engine, Base, get_db
from . import models
# We will import services later as we implement them
# from .services import vision, llm, export

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Setup CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files to serve images
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/upload")
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

@app.get("/papers")
def list_papers(db: Session = Depends(get_db)):
    return db.query(models.Paper).order_by(models.Paper.created_at.desc()).all()

@app.get("/papers/{paper_id}")
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    # Return with sorted questions
    return {
        "paper": paper,
        "questions": sorted(paper.questions, key=lambda q: q.order_index)
    }

# Placeholders for the complex logic endpoints
@app.post("/process/{paper_id}")
def process_paper(paper_id: int, db: Session = Depends(get_db)):
    print(f"Processing paper {paper_id}")
    paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    if paper.is_processed:
        return {"message": "Already processed"}

    # Output directory for crops
    # We'll put them in same folder as upload for simplicity: static/uploads
    # But ideally maybe static/uploads/{paper_id}/
    
    try:
        # Resolve absolute path to avoid cv2 issues with relative paths
        abs_file_path = os.path.abspath(paper.file_path)
        abs_upload_dir = os.path.abspath(UPLOAD_DIR)
        
        print(f"Vision processing: {abs_file_path}")
        results = vision.process_image(abs_file_path, abs_upload_dir)
        
        for idx, res in enumerate(results):
            q = models.Question(
                paper_id=paper.id,
                image_path=f"static/uploads/{res['image_filename']}", # Web accessible path
                bbox_json=str(res['bbox']),
                ocr_text=res['ocr_text'],
                order_index=idx + 1
            )
            db.add(q)
        
        paper.is_processed = True
        db.commit()
        return {"status": "completed", "questions_found": len(results)}
        
    except Exception as e:
        print(f"Error processing paper: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/solve/{question_id}")
def solve_question(question_id: int, db: Session = Depends(get_db)):
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
        
    # Call LLM
    start_text = q.ocr_text if q.ocr_text else "Identify this question from image."
    # If we wanted to send image to LLM, we'd do it here. For now, text only.
    
    solution = llm.solve_question(start_text)
    q.solution_text = solution
    db.commit()
    
    return {"solution": solution}

@app.get("/export/{paper_id}")
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
